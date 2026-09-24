"""Browser portal journeys against real Edge handlers and PostgreSQL.

Auth/storage use the local Supabase harness. The prepared revision fixture stands
in for a completed public test; GitHub scheduling is exercised separately.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from pathlib import Path
import subprocess
import time
import urllib.request
import uuid

import pytest
from playwright.sync_api import sync_playwright, expect
from psycopg.types.json import Jsonb

from test_project_http import edge_stack, run_setup, free_port, ROOT, anon_key  # noqa: F401
from test_project_database import query
from test_project_database import rpc
from project_platform.artifacts import pack_files
from project_platform.package import ProjectFile

pytestmark=pytest.mark.skipif(not os.environ.get('OBSERVER_DENO_BIN') or not os.environ.get('SAC_POSTGREST_BIN') or
    not os.environ.get('SAC_NODE_BIN'),reason='Explicit local browser test toolchain required')


@pytest.fixture(scope='module')
def portal_site(edge_stack):
    port=free_port();base=f'http://127.0.0.1:{port}'
    env={**os.environ,'PATH':os.environ['SAC_NODE_BIN']+':'+os.environ['PATH'],
         'VITE_SUPABASE_URL':edge_stack['harness'].url,'VITE_SUPABASE_ANON_KEY':anon_key(),
         'VITE_BASE_PATH':'/','VITE_SITE_URL':base}
    built=subprocess.run(['npm','run','build'],cwd=ROOT/'web',env=env,capture_output=True,text=True,timeout=180)
    assert built.returncode==0,built.stdout[-1500:]+built.stderr[-1500:]
    process=subprocess.Popen(['npm','exec','vite','--','preview','--host','127.0.0.1','--port',str(port),'--strictPort'],
        cwd=ROOT/'web',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:urllib.request.urlopen(base,timeout=1).close();break
            except OSError:time.sleep(.1)
        else:pytest.fail('Portal site did not start')
        yield base
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait()


def test_participant_link_zip_review_key_and_legacy_csv_journey(portal_site,run_setup,tmp_path):
    s=run_setup;uri=s['uri'];password='local-browser-test-password-92'
    legacy=uuid.uuid4()
    query(uri,"insert into public.phases(id,slug,name_en,name_zh) values(%s,%s,'Practice','练习赛')",(legacy,str(legacy)))
    query(uri,'insert into public.phase_scenarios values(%s,%s)',(legacy,s['scenario']))
    query(uri,'update auth.users set raw_user_meta_data=raw_user_meta_data || %s where id=%s',
          (Jsonb({'password_hash':hashlib.sha256(password.encode()).hexdigest()}),s['user']))
    # The HTTP fixture opens a run for session tests. This portal journey needs no
    # active batch until the participant presses Evaluate.
    query(uri,"update public.observer_runs set status='failed' where id=%s",(s['run'],))
    query(uri,"update public.observer_batches set status='failed' where id=(select batch_id from public.observer_runs where id=%s)",(s['run'],))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel=os.environ.get('OBSERVER_BROWSER_CHANNEL'))
        context=browser.new_context(viewport={'width':1365,'height':950},locale='en-US')
        page=context.new_page();script_errors=[];page.on('pageerror',lambda e:script_errors.append(str(e)))
        # Route the Supabase function URL to the actual local Deno server. Request
        # bodies, bearer authorization and responses are untouched, not mocked.
        page.route('**/functions/v1/observer-portal',lambda route:route.fulfill(response=route.fetch(url=s['stack']['urls']['observer-portal'])))
        page.goto(portal_site+'/register?mode=login&lang=en')
        page.get_by_test_id('login-email').fill(f"{s['user']}@example.test")
        page.get_by_test_id('login-password').fill(password)
        page.get_by_test_id('login-submit').click()
        expect(page).to_have_url(portal_site+'/dashboard',timeout=20000)
        page.get_by_role('link',name='Agent projects',exact=True).click()
        expect(page.get_by_test_id('project-title')).to_be_visible(timeout=15000)
        page.get_by_test_id('project-title').fill('Repository project')
        page.get_by_test_id('project-url').fill('https://github.com/owner/project')
        page.get_by_test_id('project-submit').click()
        expect(page.get_by_role('heading',name='Repository project',exact=True)).to_be_visible(timeout=15000)
        revision=query(uri,'select r.id from public.observer_revisions r join public.observer_projects p on p.id=r.project_id where p.team_id=%s and p.title=%s',
                       (s['team'],'Repository project'))[0][0]
        query(uri,"""insert into private.observer_installations(organization,organization_id,installation_id,repository_id,approved_sha,enabled)
          values('AGENTIC-OBSERVER26-runner-1','101',202,'303',%s,true)""",('a'*40,))
        job=uuid.uuid4();nonce=secrets.token_urlsafe(32)
        rpc(uri,'observer_enqueue_job',job,'prepare',None,revision,'AGENTIC-OBSERVER26-runner-1',nonce,'private input','private nonce')
        rpc(uri,'observer_claim_job',job,nonce,'404','1','303','101','a'*40)
        rpc(uri,'observer_finish_job',job,'404','1',{'diagnostics':{'code':'completed','log':'Compiler output <script>alert(1)</script>'}},'')
        page.get_by_role('button',name='Private run logs',exact=True).first.click()
        logs=page.get_by_test_id('project-diagnostics')
        expect(logs.locator('pre')).to_have_text('Compiler output <script>alert(1)</script>',timeout=15000)
        assert 'private input' not in page.content()
        logs.get_by_role('button',name='Close review',exact=True).click()
        manifest={'schema_version':'observer-project-v1','image':'python@sha256:'+'c'*64,'run':['python','agent.py']}
        query(uri,"""update public.observer_revisions set status='reviewable',source_digest=%s,approval_digest=%s,
          manifest=%s,adapter_files=%s,public_test='{"passed":true}',explanation='Calls the submitted strategy.' where id=%s""",
          ('a'*64,'b'*64,Jsonb(manifest),Jsonb({'.observer-adapter/main.py':'# <script>alert(1)</script>\nimport agent'}),revision))
        page.get_by_role('button',name='Refresh',exact=True).click()
        page.get_by_role('button',name='Review interface',exact=True).click()
        expect(page.get_by_test_id('project-approve')).to_be_disabled()
        expect(page.locator('pre').filter(has_text='<script>')).to_have_count(1)
        page.get_by_test_id('project-confirm').check()
        page.get_by_test_id('project-approve').click()
        expect(page.get_by_role('button',name='Evaluate confirmed version')).to_be_visible(timeout=15000)
        assert query(uri,'select status from public.observer_revisions where id=%s',(revision,))==[('approved',)]
        page.get_by_role('radio',name='Private ZIP upload',exact=True).check()
        page.get_by_test_id('project-title').fill('ZIP project')
        page.get_by_test_id('project-zip').set_input_files({'name':'project.zip','mimeType':'application/zip',
            'buffer':pack_files((ProjectFile('main.rs',b'fn main() {}'),))})
        page.get_by_test_id('project-submit').click()
        expect(page.get_by_role('heading',name='ZIP project',exact=True)).to_be_visible(timeout=15000)
        api=page.locator('form').filter(has=page.get_by_role('button',name='Save encrypted key',exact=True))
        api.get_by_label('API name',exact=True).fill('Private provider')
        api.get_by_label('Model names, separated by commas').fill('test-model')
        api.get_by_label('API key',exact=True).fill('not-a-real-key-browser-fixture')
        api.get_by_role('button',name='Save encrypted key',exact=True).click()
        expect(page.get_by_test_id('project-api-key')).to_have_value('')
        expect(page.get_by_text('Private provider',exact=True)).to_be_visible(timeout=15000)
        assert 'not-a-real-key-browser-fixture' not in page.content()
        page.get_by_role('button',name='Review interface',exact=True).click()
        page.get_by_label('Architecture and reproduction notes').fill('Run the project using the submitted manifest.')
        page.get_by_role('button',name='Save evidence',exact=True).click()
        expect(page.get_by_role('status').filter(has_text='Saved.')).to_be_visible(timeout=15000)
        # The scheduler normally opens this local session. Its credential is
        # encrypted in the real database, then delivered through the real portal.
        batch=rpc(uri,'observer_create_batch',s['phase'],None,role='authenticated',user=s['user'])
        local_run=query(uri,'select id from public.observer_runs where batch_id=%s',(batch,))[0][0]
        participant=secrets.token_urlsafe(32);engine=secrets.token_urlsafe(32)
        credential=f'obs_{local_run}.{participant}'
        encrypted=subprocess.run([os.environ['OBSERVER_DENO_BIN'],'eval',
            'import {encryptCredential} from "./_shared/observer-model.ts"; '
            'const d=await new Response(Deno.stdin.readable).json(); console.log(await encryptCredential(d.key,d.id,d.master));'],
            cwd=ROOT/'supabase/functions',input=json.dumps({'key':credential,'id':str(local_run)+':local','master':s['stack']['master']}),
            capture_output=True,text=True,check=True).stdout.strip()
        rpc(uri,'observer_open_local_session',local_run,participant,engine,encrypted)
        page.get_by_role('button',name='Refresh',exact=True).click()
        page.get_by_role('button',name='Local run instructions',exact=True).click()
        panel=page.get_by_test_id('local-instructions')
        expect(panel.get_by_label('Temporary run credential',exact=True)).to_have_value(credential)
        expect(panel.get_by_label('Temporary run credential',exact=True)).to_have_attribute('type','password')
        assert engine not in page.content()
        with page.expect_download() as downloaded:
            panel.get_by_role('link',name='Download local runner',exact=True).click()
        archive=tmp_path/'runner.zip';downloaded.value.save_as(archive)
        import zipfile
        with zipfile.ZipFile(archive) as bundle:
            assert 'observer-local-runner/project_platform/local.py' in bundle.namelist()
            assert not any(name.endswith(('.csv','.env')) for name in bundle.namelist())
            bundle.extractall(tmp_path/'unpacked')
        import sys
        smoke=subprocess.run([sys.executable,'-m','project_platform.local','--help'],
            cwd=tmp_path/'unpacked/observer-local-runner',capture_output=True,text=True)
        assert smoke.returncode==0,smoke.stderr
        page.set_viewport_size({'width':390,'height':844})
        page.goto(portal_site+'/projects?lang=zh')
        expect(page.get_by_role('heading',name='智能体项目',exact=True)).to_be_visible(timeout=15000)
        expect(page.get_by_role('heading',name='ZIP project',exact=True)).to_be_visible(timeout=15000)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        shots=ROOT/'artifacts/screenshots-projects';shots.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(shots/'portal-mobile.png'),full_page=True)
        page.get_by_role('link',name='原有 CSV 提交',exact=True).click()
        expect(page.get_by_test_id('submit-kind-results')).to_be_visible(timeout=15000)
        expect(page.get_by_test_id('submit-phase')).to_have_value(str(legacy))
        expect(page.get_by_test_id('online-submission-link')).to_be_visible()
        expect(page.get_by_test_id('submit-phase').locator('option[value="'+str(s['phase'])+'"]')).to_have_count(0)
        page.goto(portal_site+'/submit?phase='+str(s['phase'])+'&lang=zh')
        expect(page).to_have_url(portal_site+'/projects',timeout=15000)
        expect(page.get_by_test_id('project-title')).to_be_visible()
        assert not script_errors,script_errors
        context.close();browser.close()


def test_online_board_shows_same_batch_mean_and_keeps_private_artifacts_hidden(portal_site,run_setup):
    s=run_setup;uri=s['uri'];batch=query(uri,'select batch_id from public.observer_runs where id=%s',(s['run'],))[0][0]
    query(uri,"update public.observer_runs set status='scored',score=60,score_summary=%s,result_path='github:private-board-result',finished_at=now() where id=%s",
      (Jsonb({'score':{'total':60,'base_science':70,'program_bonus':0,'request_reward':0,'penalties':{'bad':10}},'completed_tiles':4,'required_missing':2}),s['run']))
    query(uri,'select private.observer_finalize_batch(%s)',(batch,))
    query(uri,'update public.phases set counts_for_final=(id=%s)',(s['phase'],))
    team_name=query(uri,'select name from public.teams where id=%s',(s['team'],))[0][0]
    slug=query(uri,'select slug from public.phases where id=%s',(s['phase'],))[0][0]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel=os.environ.get('OBSERVER_BROWSER_CHANNEL'))
        page=browser.new_page(viewport={'width':1365,'height':950});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(portal_site+'/leaderboard/'+slug+'?lang=en')
        row=page.get_by_test_id('lb-row').filter(has_text=team_name)
        expect(row).to_be_visible(timeout=15000)
        expect(row.locator('td').nth(2)).to_contain_text('60')
        row.click();dialog=page.get_by_test_id('team-detail')
        expect(dialog).to_be_visible()
        expect(dialog).to_contain_text('60')
        assert 'private-board-result' not in page.content()
        page.keyboard.press('Escape')
        page.goto(portal_site+'/?lang=en')
        expect(page.locator('#board').get_by_test_id('lb-row').filter(has_text=team_name)).to_be_visible(timeout=15000)
        assert not errors,errors
        browser.close()
