#!/usr/bin/env python3
"""Browser acceptance against the deployed backend and a local production build.

Uses the synthetic Keychain identity in an isolated browser profile. Reads its
existing accepted project; it does not submit work or alter real participants.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request
import zipfile

from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node-bin',required=True)
    parser.add_argument('--browser-channel',default='chrome')
    parser.add_argument('--case',default='python-v2')
    args=parser.parse_args()
    state=json.loads(subprocess.check_output(['security','find-generic-password','-s','agentic-observer26-backend',
      '-a',os.environ['SUPABASE_PROJECT_REF'],'-w'],text=True))
    lab=state['lab']
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','TMPDIR','LANG')}
    env.update({'PATH':args.node_bin+':'+env['PATH'],'VITE_SUPABASE_URL':os.environ['SUPABASE_URL'],
      'VITE_SUPABASE_ANON_KEY':os.environ['SUPABASE_ANON_KEY'],'VITE_BASE_PATH':'/','VITE_SITE_URL':base})
    build=subprocess.run(['npm','run','build'],cwd=ROOT/'web',env=env,capture_output=True,text=True,timeout=180)
    if build.returncode:raise RuntimeError('Local production build failed')
    process=subprocess.Popen(['npm','exec','vite','--','preview','--host','127.0.0.1','--port',str(port),'--strictPort'],
      cwd=ROOT/'web',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:urllib.request.urlopen(base,timeout=1).close();break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('Local preview failed to start')
        with sync_playwright() as pw, tempfile.TemporaryDirectory(prefix='observer-browser-result-') as temporary:
            browser=pw.chromium.launch(channel=args.browser_channel)
            context=browser.new_context(viewport={'width':1365,'height':950},locale='en-US')
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base+'/register?mode=login&lang=en')
            page.get_by_test_id('login-email').fill(lab['email'])
            page.get_by_test_id('login-password').fill(lab['password'])
            page.get_by_test_id('login-submit').click()
            expect(page).to_have_url(base+'/dashboard',timeout=45000)
            page.get_by_role('link',name='Agent projects',exact=True).click()
            project=page.locator('article').filter(has=page.get_by_role('heading',name='Acceptance '+args.case,exact=True))
            expect(project).to_be_visible(timeout=45000)
            project.get_by_role('button',name='Private run logs',exact=True).click()
            logs=page.get_by_test_id('project-diagnostics')
            expect(logs).to_contain_text('MODEL_PROXY_OK ISOLATION_OK',timeout=30000)
            project.get_by_role('button',name='Review interface',exact=True).click()
            review=page.get_by_test_id('project-review')
            expect(review).to_contain_text('Public scenario test passed',timeout=15000)
            with page.expect_download(timeout=45000) as downloaded:
                review.get_by_role('button',name='Download public test result',exact=True).click()
            archive=Path(temporary)/'result.zip';downloaded.value.save_as(archive)
            with zipfile.ZipFile(archive) as zipped:
                assert any(n.endswith('/decisions.csv') or n=='decisions.csv' for n in zipped.namelist())
            for secret in (state['model_key'],state['master'],state['dispatch']):
                assert secret not in page.content()
            page.set_viewport_size({'width':390,'height':844})
            page.goto(base+'/projects?lang=zh')
            expect(page.get_by_role('heading',name='智能体项目',exact=True)).to_be_visible(timeout=30000)
            expect(page.get_by_role('heading',name='Acceptance '+args.case,exact=True)).to_be_visible(timeout=30000)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
            shots=ROOT/'artifacts/screenshots-projects';shots.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(shots/'live-portal-mobile.png'),full_page=True)
            page.get_by_role('link',name='原有 CSV 提交',exact=True).click()
            expect(page.get_by_test_id('submit-kind-results')).to_be_visible(timeout=30000)
            assert not errors,'Browser script errors occurred'
            context.close();browser.close()
        print(json.dumps({'backend':'deployed','frontend':'local production build','login':'passed',
          'private_logs':'passed','public_test_download':'passed','mobile_zh':'passed','legacy_csv':'passed','browser_errors':0}))
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait()


if __name__=='__main__':main()
