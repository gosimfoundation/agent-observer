"""Smoke acceptance: one tiny project through the formal path in a few minutes.

Uses its OWN hidden platform-test team, account, private 7-night scenario and
team-restricted internal phase (never the full acceptance team 72fe0b30 or its
phase). Setup is idempotent and follows scripts/configure-observer-acceptance.py
(same phase shape, reused functions); differences, all confined to this phase:
one scenario instead of two, runtime 10 s (the platform minimum), and a
calibration profile whose bounds accept the first random candidate, so a
randomized instance is still generated, measured and recorded, in ~2 s.

Checks: submission accepted -> public test passed -> approved -> randomized
instance recorded -> evaluation terminal -> calibrated score recorded.
The project is a stdlib Python agent that never calls a model (no key needed).
Nothing printed here is a credential. Exit code 0 only when every step passes.
"""
import importlib.util, io, json, os, secrets, sys, time, urllib.error, urllib.parse, urllib.request, uuid, zipfile
from argparse import Namespace
from pathlib import Path

MAIN = Path(os.environ.get('MAIN_TREE', '/tmp/main'))
sys.path.insert(0, str(MAIN))
spec = importlib.util.spec_from_file_location('acc', MAIN / 'scripts/configure-observer-acceptance.py')
acc = importlib.util.module_from_spec(spec); spec.loader.exec_module(acc)

BASE = os.environ['SUPABASE_URL']; ANON = os.environ['SUPABASE_ANON_KEY']; SERVICE = os.environ['SUPABASE_SERVICE_ROLE_KEY']
EMAIL = 'observer-platform-smoke@create.gosim.org'
TEAM_NAME = 'Observer platform smoke test'
SCENARIO_SLUG = 'observer-platform-smoke-1'
FULL_ACCEPTANCE_TEAM = '72fe0b30-2c9b-48b6-b546-5a0c3dc9b101'
RUNTIME_SECONDS = 10  # check (runtime_seconds between 10 and 18000)
OUT = Path('ops-runner/results/smoke'); OUT.mkdir(parents=True, exist_ok=True)
DEADLINE_MIN = float(os.environ.get('SMOKE_MINUTES', '15'))
T0 = time.time()
steps = []
report = {'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'steps': steps}


def q(v): return acc.quote(v)


def sql(statement):  # rows as dicts
    return acc.request('https://api.supabase.com', '/v1/projects/' + os.environ['SUPABASE_PROJECT_REF'] + '/database/query',
                       {'query': statement}, token=os.environ['SUPABASE_ACCESS_TOKEN']) or []


def http(url, data=None, method=None, token=None, headers=None):
    body = data if isinstance(data, bytes) else None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method=method, headers={
        'apikey': ANON, 'Authorization': 'Bearer ' + (token or ANON),
        'Content-Type': 'application/zip' if isinstance(data, bytes) else 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = r.read(); return json.loads(out) if out else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code} {url.split("?")[0].replace(BASE, "")}: {e.read()[:300].decode("utf8", "replace")}') from None


last = [T0]
kicks = {'n': 0, 'at': 0.0}


def kick(rid):
    """Run the platform dispatcher now instead of waiting for its 1-minute cron.

    Same effect as the lab's manual tick: private.observer_tick() posts to the
    dispatcher with its Vault capability (which never leaves the database). The
    dispatcher is idempotent and lock-safe. Only kicks while none of this
    revision's jobs is in flight (i.e. the next step waits on the dispatcher),
    at most every 8 s.
    """
    if time.time() - kicks['at'] < 8: return
    try:
        busy = sql("select count(*) as n from private.observer_jobs j where j.status in ('dispatched','claimed') and (j.revision_id="
                   + q(rid) + " or j.run_id in (select r.id from public.observer_runs r join public.observer_batches b on b.id=r.batch_id"
                   " where b.revision_id=" + q(rid) + "))")[0]['n']
        if busy: return
        kicks['at'] = time.time()
        sql('update private.observer_dispatch_config set last_enqueued_at=null where id and enabled;select private.observer_tick()')
        kicks['n'] += 1
    except Exception as error:
        print('  kick failed:', str(error)[:120], flush=True)


def step(name, **data):
    now = time.time()
    entry = {'step': name, 't': round(now - T0, 1), 'took': round(now - last[0], 1), **data}
    last[0] = now; steps.append(entry); print(json.dumps(entry, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------- setup
def ensure_scenario():
    rows = sql('select id from public.scenarios where slug=' + q(SCENARIO_SLUG))
    if rows:
        scenario_id = rows[0]['id']
    else:
        scenario_id = str(uuid.uuid4())
        # Inactive like the lab's private scenarios: never listed, never public.
        sql("insert into public.scenarios(id,slug,name,is_active,weather_public,forecasts_public,events_public,n_nights) values("
            + ','.join(map(q, (scenario_id, SCENARIO_SLUG, 'Private smoke scenario'))) + ",false,false,false,false,7)")
    if acc.query('select 1 from public.phase_scenarios ps join public.phases p on p.id=ps.phase_id where ps.scenario_id=' + q(scenario_id)
                  + " and (p.counts_for_final or p.slug in ('online','practice','observer-platform-e2e'))"):
        raise RuntimeError('smoke scenario is linked to a participant phase')
    bundle = sql('select storage_path,digest from private.observer_scenario_bundles where scenario_id=' + q(scenario_id))
    profile = sql('select id from private.observer_calibration_profiles where scenario_id=' + q(scenario_id) + ' order by created_at limit 1')
    if bundle and profile:
        return scenario_id, profile[0]['id']
    if bundle or profile:
        raise RuntimeError('smoke scenario half configured; inspect it before continuing')
    import hashlib, tempfile
    from challenge.scenario_builder import generate_scenario
    from project_platform.artifacts import pack_files
    from project_platform.package import ProjectFile
    from project_platform.scenario_instances import directory_digest, PANEL_VERSION
    with tempfile.TemporaryDirectory(prefix='smoke-scenario-') as root:
        scenario = Path(root) / 'scenario'
        generate_scenario(scenario, scenario_id=SCENARIO_SLUG, seed=901, days=7, start_date='2026-10-05', global_wallclock_seconds=300)
        template_digest = directory_digest(scenario)
        data = pack_files([ProjectFile(p.relative_to(scenario).as_posix(), p.read_bytes()) for p in sorted(scenario.rglob('*')) if p.is_file()])
    digest = hashlib.sha256(data).hexdigest(); path = scenario_id + '/' + digest + '.zip'
    http(BASE + '/storage/v1/object/observer-scenarios/' + path, data, token=SERVICE, headers={'x-upsert': 'false'})
    sql('insert into private.observer_scenario_bundles(scenario_id,storage_path,digest) values(' + ','.join(map(q, (scenario_id, path, digest))) + ')')
    # Bounds wide enough that candidate 0 always qualifies: the instance is still
    # randomly generated, measured by the reference panel and recorded, just fast.
    wide = [-1e12, 1e12]
    profile = {'schema_version': 'observer-calibration-profile-v1', 'panel_version': PANEL_VERSION, 'template_digest': template_digest,
               'bounds': {'span': [1e-9, 1e15], 'open_fraction': [0, 1], 'gain_rate': wide, 'required_first': wide, 'requests_first': wide},
               'note': 'smoke test only: accepts the first candidate'}
    pid = sql('insert into private.observer_calibration_profiles(scenario_id,bundle_digest,profile) values('
              + q(scenario_id) + ',' + q(digest) + ',' + q(json.dumps(profile)) + '::jsonb) returning id')[0]['id']
    return scenario_id, pid


def ensure_account():
    users = sql("select id,raw_user_meta_data->>'observer_platform_e2e' as marker from auth.users where email=" + q(EMAIL))
    if users:
        if users[0]['marker'] != 'true': raise RuntimeError('refusing to use an existing non-test account')
        user = users[0]['id']
    else:
        user = http(BASE + '/auth/v1/admin/users', {'email': EMAIL, 'password': secrets.token_urlsafe(32), 'email_confirm': True,
                    'user_metadata': {'full_name': TEAM_NAME, 'observer_platform_e2e': True}}, token=SERVICE)['id']
    # Platform test account: off the player wall and in the excluded accounts.
    sql("begin;update public.profiles set show_on_wall=false where id=" + q(user) + ";"
        "insert into public.site_settings(key,value) values('excluded_accounts',jsonb_build_array(" + q(user) + "::text)) "
        "on conflict(key) do update set value=case when public.site_settings.value @> excluded.value then public.site_settings.value "
        "else public.site_settings.value || excluded.value end;commit;")
    team = sql('select team_id from public.profiles where id=' + q(user))[0]['team_id']
    if not team:
        # Created hidden in one transaction (create_team would show it for a moment).
        team = sql("with t as (insert into public.teams(name,slug,leader_id,max_size,project_idea,github_repo,is_hidden) values("
                   + ','.join(map(q, (TEAM_NAME, 'observer-platform-smoke-test', user))) + ",1,'Private automated smoke tests','',true) returning id) "
                   "update public.profiles set team_id=(select id from t),looking_for_team=false where id=" + q(user) + " returning team_id")[0]['team_id']
    if team == FULL_ACCEPTANCE_TEAM: raise RuntimeError('smoke account belongs to the full acceptance team')
    sql('update public.teams set is_hidden=true where id=' + q(team) + ' and not is_hidden')
    return user, team


def ensure_phase(team, scenario_id, profile_id):
    info = acc.check_team(team)
    scenario = {'scenario_id': scenario_id}
    scenario.update(zip(('bundle_path', 'bundle_digest'), acc.query(
        'select storage_path,digest from private.observer_scenario_bundles where scenario_id=' + q(scenario_id))[0]))
    args = Namespace(runtime_seconds=RUNTIME_SECONDS, daily_batches=100, sort_order=10110)
    plan = acc.plan_phase(info, [scenario], args, {scenario_id: profile_id})
    ready = acc.query('select 1 from private.observer_scenario_calibration where phase_id=' + q(plan['phase_id']))
    if not ready:  # roster and calibration freeze after the first formal batch, so write them once
        for statement in plan['statements']: acc.query(statement)
    else:  # keep runtime/limits current without touching the frozen roster
        acc.query(plan['statements'][1])
    acc.verify(plan['phase_id'])
    return plan['phase_id']


# ---------------------------------------------------------------- project
AGENT = '''import json, sys
for line in sys.stdin:
    m = json.loads(line)
    if m.get('message_type') != 'decision_request':
        continue
    tiles = [t for t in m['payload']['candidate_tiles'] if t['effective_weather']['is_observable'] and not t.get('already_completed')]
    t = tiles[0] if tiles else None
    print(json.dumps({'protocol_version': m['protocol_version'], 'message_type': 'decision_response',
        'decision_sequence': m['decision_sequence'], 'action': 'observe' if t else 'wait',
        'tile_id': t['tile_id'] if t else '', 'program': 'BACKUP' if t else ''}), flush=True)
'''


def project_zip():
    files = {'README.md': '# Smoke test project\nFirst open tile, BACKUP program, no model.\n', 'src/agent.py': AGENT,
             'observer.project.json': json.dumps({'schema_version': 'observer-project-v1', 'image': 'python:3.12-slim',
                                                  'run': ['python3', '-u', 'src/agent.py']})}
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items(): archive.writestr(name, content)
    return data.getvalue()


def fast_setup():
    """One query: is everything from a previous setup still in place? (ids or None)"""
    rows = sql("""select u.id as user_id,t.id as team_id,p.id as phase_id from auth.users u
      join public.profiles pr on pr.id=u.id and not pr.is_banned and not pr.show_on_wall
      join public.teams t on t.id=pr.team_id and t.is_hidden and t.name=""" + q(TEAM_NAME) + """
      join public.phases p on p.slug='observer-acceptance-'||left(t.id::text,8) and p.is_active
        and not p.counts_for_final and p.leaderboard_mode='hidden'
      join public.observer_phase_settings c on c.phase_id=p.id and c.access_team_id=t.id and c.projects_enabled
        and not c.local_sessions_enabled and c.runtime_seconds=""" + str(RUNTIME_SECONDS) + """
      join public.scenarios s on s.slug=""" + q(SCENARIO_SLUG) + """ and not s.is_active
      join private.observer_scenario_calibration k on k.phase_id=p.id and k.scenario_id=s.id
      where u.email=""" + q(EMAIL) + """ and u.raw_user_meta_data->>'observer_platform_e2e'='true'
        and (select count(*) from public.phase_scenarios ps where ps.phase_id=p.id)=1
        and exists(select 1 from public.site_settings x where x.key='excluded_accounts' and x.value ? u.id::text)""")
    return (rows[0]['user_id'], rows[0]['team_id'], rows[0]['phase_id']) if len(rows) == 1 else None


def main():
    found = fast_setup()
    if found:
        user, team, phase = found
        acc.verify(phase)  # still invisible to anonymous visitors
    else:
        scenario_id, profile_id = ensure_scenario()
        user, team = ensure_account()
        phase = ensure_phase(team, scenario_id, profile_id)
    if team == FULL_ACCEPTANCE_TEAM: raise RuntimeError('smoke account belongs to the full acceptance team')
    report.update(team=team[:8], phase=phase[:8], scenario=SCENARIO_SLUG)
    email = http(f'{BASE}/auth/v1/admin/users/{user}', token=SERVICE)['email']
    password = secrets.token_urlsafe(24)
    http(f'{BASE}/auth/v1/admin/users/{user}', {'password': password}, method='PUT', token=SERVICE)
    token = http(f'{BASE}/auth/v1/token?grant_type=password', {'email': email, 'password': password})['access_token']
    del password

    def portal(action, **kw):
        return http(f'{BASE}/functions/v1/observer-portal', {'action': action, **kw}, token=token)['data']
    step('setup', team=team[:8], phase=phase[:8], reused=bool(found))

    # A leftover active batch from an aborted smoke run would block evaluate.
    listing = portal('list')
    active = [b['id'] for b in listing['batches'] if b['status'] in ('queued', 'running')]
    if active: raise RuntimeError('smoke team already has an active batch ' + active[0][:8] + '; wait for it to finish')

    slot = portal('upload', purpose='source')
    http(f'{BASE}/storage/v1/object/upload/sign/observer-staging/' + urllib.parse.quote(slot['path'], safe='/')
         + '?token=' + urllib.parse.quote(slot['token'], safe=''), project_zip(), method='PUT', token=token)
    rid = portal('submit_zip', title='Smoke ' + time.strftime('%m%d-%H%M'), upload_id=slot['id'])['revision_id']
    report['revision'] = rid
    step('submission_accepted', revision=rid[:8])

    deadline = T0 + DEADLINE_MIN * 60
    seen = None
    while True:
        rev = next(r for p in portal('list')['projects'] for r in p['observer_revisions'] if r['id'] == rid)
        if rev['status'] != seen:
            seen = rev['status']; print(f'  revision {seen} at +{time.time() - T0:.0f}s', flush=True)
        test = rev.get('public_test') or {}
        if rev['status'] == 'reviewable' and test.get('passed'):
            step('public_test_passed', public_test_score=test.get('score')); break
        if rev['status'] == 'failed':
            report['diagnostics'] = [{k: j.get(k) for k in ('kind', 'status', 'code')} | {'log': (j.get('log') or '')[-800:]}
                                     for j in portal('diagnostics', revision_id=rid)]
            raise RuntimeError('public test failed: ' + (rev.get('error') or '') + ' ' + json.dumps(test)[:300])
        if time.time() > deadline: raise TimeoutError('public test still ' + rev['status'])
        kick(rid); time.sleep(3)

    portal('approve', revision_id=rid, digest=rev['approval_digest'])
    step('approved')
    bid = portal('evaluate', revision_id=rid, phase_id=phase)['batch_id']
    report['batch'] = bid
    step('evaluation_queued', batch=bid[:8])

    run_id = recorded = None
    while True:
        batch = next((b for b in portal('list')['batches'] if b['id'] == bid), None)
        runs = (batch or {}).get('observer_runs') or []
        if runs and not run_id:
            run_id = runs[0]['id']
        if run_id and not recorded:
            inst = sql('select recorded_at is not null as recorded,record->>\'candidate\' as candidate,'
                       'left(record->>\'instance_digest\',12) as instance from private.observer_scenario_instances where run_id=' + q(run_id))
            if inst and inst[0]['recorded']:
                recorded = True
                step('instance_prepared', candidate=inst[0]['candidate'], instance=inst[0]['instance'])
        if batch and batch['status'] in ('scored', 'failed', 'cancelled'):
            if not recorded: step('instance_prepared', missing=True)
            step('evaluation_terminal', status=batch['status'],
                 runs=[{k: r.get(k) for k in ('status', 'score', 'error')} for r in runs])
            break
        if time.time() > deadline: raise TimeoutError('batch still ' + (batch or {}).get('status', '?'))
        kick(rid); time.sleep(3)

    run = sql('select r.status,r.score,r.score_summary->\'calibration\'->>\'adjusted_score\' as adjusted,'
              'r.score_summary->\'raw_score\'->>\'total\' as raw,r.score_summary->>\'termination_reason\' as termination,'
              'r.score_summary->>\'committed_action_count\' as actions,b.score as batch_score '
              'from public.observer_runs r join public.observer_batches b on b.id=r.batch_id where r.id=' + q(run_id))[0]
    if batch['status'] != 'scored' or run['score'] is None or run['adjusted'] is None or batch.get('score') is None:
        report['diagnostics'] = [{k: j.get(k) for k in ('kind', 'status', 'code')} | {'log': (j.get('log') or '')[-800:]}
                                 for j in portal('diagnostics', run_id=run_id)]
        raise RuntimeError('no calibrated score recorded: ' + json.dumps(run, default=str))
    step('score_recorded', score=run['score'], raw=run['raw'], termination=run['termination'], actions=run['actions'])


def breakdown():
    """Where the time went, from the platform's own job timestamps."""
    rid = report.get('revision')
    if not rid: return
    rows = sql("""select 'prepare' as job,j.status,j.created_at,j.claimed_at,j.finished_at from private.observer_jobs j where j.revision_id=""" + q(rid) + """
      union all select b.purpose||':'||j.kind,j.status,j.created_at,j.claimed_at,j.finished_at from private.observer_jobs j
        join public.observer_runs r on r.id=j.run_id join public.observer_batches b on b.id=r.batch_id
        where b.revision_id=""" + q(rid) + """ order by 3""")
    from datetime import datetime
    ts = lambda v: datetime.fromisoformat(str(v).replace(' ', 'T').replace('Z', '+00:00')).timestamp() if v else None
    report['jobs'] = []
    for r in rows:
        c, k, f = ts(r['created_at']), ts(r['claimed_at']), ts(r['finished_at'])
        report['jobs'].append({'job': r['job'], 'status': r['status'], 'queue_s': round(k - c) if k else None,
                               'work_s': round(f - k) if f and k else None, 'start_t': round(c - T0) if c else None})


ok = False
try:
    main(); ok = True
except Exception as error:
    report['error'] = str(error)[:500]
    print('SMOKE FAILED:', report['error'], flush=True)
try:
    breakdown()
except Exception as error:
    report['breakdown_error'] = str(error)[:200]
report['ok'] = ok; report['dispatch_kicks'] = kicks['n']; report['total_s'] = round(time.time() - T0, 1)

print('\n==================== SMOKE ACCEPTANCE ' + ('PASSED' if ok else 'FAILED') + ' ====================')
print(f"team {report.get('team')}  phase {report.get('phase')}  scenario {SCENARIO_SLUG}  runtime {RUNTIME_SECONDS}s")
for s in steps:
    extra = ', '.join(f'{k}={v}' for k, v in s.items() if k not in ('step', 't', 'took'))
    print(f"  {s['step']:<22} +{s['t']:>6.1f}s  (step {s['took']:>6.1f}s)  {extra}"[:160])
for j in report.get('jobs', []):
    print(f"    job {j['job']:<18} {j['status']:<9} created +{j['start_t']}s  queued {j['queue_s']}s  ran {j['work_s']}s")
if not ok: print('  ERROR:', report['error'])
for d in report.get('diagnostics', []):
    print('  diag', d.get('kind'), d.get('status'), d.get('code'), '|', (d.get('log') or '')[-300:].replace('\n', ' | '))
print(f"  total {report['total_s']}s (target < 600s), dispatcher kicks {kicks['n']}")
(OUT / 'last.json').write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str))
with (OUT / 'history.jsonl').open('a') as h: h.write(json.dumps(report, ensure_ascii=False, default=str) + '\n')
sys.exit(0 if ok else 1)
