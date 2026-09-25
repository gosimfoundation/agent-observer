"""Live acceptance on production as the hidden acceptance team.

Runs the formal path end to end in the team-restricted acceptance phase:
save the team's own model key (encrypted), submit a project, wait for the
public test, approve, evaluate on the formal scenarios, collect scores.
State (ids only, never keys or passwords) lives in ops-runner/results/acceptance.
"""
import io, json, os, secrets, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, '/tmp/main/scripts')
import importlib.util
spec = importlib.util.spec_from_file_location('live', '/tmp/main/scripts/observer-live-test.py')
live = importlib.util.module_from_spec(spec); spec.loader.exec_module(live)

BASE = os.environ['SUPABASE_URL']; ANON = os.environ['SUPABASE_ANON_KEY']; SERVICE = os.environ['SUPABASE_SERVICE_ROLE_KEY']
TEAM = '72fe0b30-2c9b-48b6-b546-5a0c3dc9b101'; PHASE = '1315ce8d-23ac-48c4-bcea-128ffbe262ad'
OUT = Path('ops-runner/results/acceptance'); OUT.mkdir(parents=True, exist_ok=True)
STATE = OUT / 'state.json'
state = json.loads(STATE.read_text()) if STATE.exists() else {'cases': {}, 'log': []}
DEADLINE = time.time() + float(os.environ.get('ACCEPT_MINUTES', '45')) * 60


def log(event, **data):
    entry = {'t': time.strftime('%H:%M:%S', time.gmtime()), 'event': event, **data}
    state['log'].append(entry); print(json.dumps(entry, ensure_ascii=False), flush=True)
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False))


def http(url, data=None, method=None, token=None, raw=False, ctype=None, headers=None):
    body = data if isinstance(data, bytes) else None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method=method, headers={
        'apikey': ANON, 'Authorization': 'Bearer ' + (token or ANON),
        'Content-Type': ctype or ('application/zip' if isinstance(data, bytes) else 'application/json'), **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = r.read(); return out if raw else (json.loads(out) if out else None)
    except urllib.error.HTTPError as e:
        text = e.read()[:400].decode('utf8', 'replace')
        raise RuntimeError(f'HTTP {e.code} {url.split("?")[0].replace(BASE, "")}: {text}') from None


# Sign in as the acceptance team's member with a fresh one-off password (never printed).
member = http(f'{BASE}/rest/v1/profiles?team_id=eq.{TEAM}&select=id&limit=1', token=SERVICE)[0]['id']
user = http(f'{BASE}/auth/v1/admin/users/{member}', token=SERVICE)
password = secrets.token_urlsafe(24)
http(f'{BASE}/auth/v1/admin/users/{member}', {'password': password}, method='PUT', token=SERVICE)
TOKEN = http(f'{BASE}/auth/v1/token?grant_type=password', {'email': user['email'], 'password': password})['access_token']
del password


def portal(action, **kw):
    return http(f'{BASE}/functions/v1/observer-portal', {'action': action, **kw}, token=TOKEN)['data']


def use_key(provider):
    if provider is None: return
    if provider == 'kimi':
        models = http('https://api.kimi.com/coding/v1/models', token=os.environ['KIMI_API_KEY'])
        model = next(m['id'] for m in models['data'])
        base, key = 'https://api.kimi.com/coding/v1', os.environ['KIMI_API_KEY']
    else:
        base, model, key = 'https://open.bigmodel.cn/api/paas/v4', 'glm-4.5-flash', os.environ['GLM_API_KEY']
    portal('set_team_model_mode', mode='stored')
    saved = portal('save_team_model', base_url=base, model=model, key=key)['team_model']['saved']
    log('key_saved', provider=provider, base=saved['base_url'], model=saved['model'], hint_len=len(saved.get('key_hint') or ''))


def upload_zip(kind):
    slot = portal('upload', purpose='source')
    http(f'{BASE}/storage/v1/object/upload/sign/observer-staging/' + urllib.parse.quote(slot['path'], safe='/')
         + '?token=' + urllib.parse.quote(slot['token'], safe=''), live.fixture(kind), method='PUT', token=TOKEN)
    return portal('submit_zip', title='Acceptance ' + kind + ' ' + time.strftime('%m%d-%H%M'), upload_id=slot['id'])


CASES = [  # name, how, provider (None = deterministic, no model)
    ('python-zip-kimi', 'python', 'kimi'),
    ('repo-glm', 'repository', 'glm'),
    ('rust-zip', 'rust', None),
]


def revision_of(rid):
    for p in portal('list')['projects']:
        for r in p['observer_revisions']:
            if r['id'] == rid: return r


def batch_of(bid):
    return next((b for b in portal('list')['batches'] if b['id'] == bid), None)


for name, how, provider in CASES:
    case = state['cases'].setdefault(name, {})
    if case.get('done'): continue
    try:
        if 'revision_id' not in case:
            use_key(provider)
            sub = portal('submit_repository', title='Acceptance repo ' + time.strftime('%m%d-%H%M'),
                         url='https://github.com/BH3GEI/observer-project-example') if how == 'repository' else upload_zip(how)
            case.update(revision_id=sub['revision_id'], provider=provider); log('submitted', case=name, how=how)
        while 'batch_id' not in case:
            r = revision_of(case['revision_id'])
            test = r.get('public_test') or {}
            if r['status'] == 'reviewable' and test.get('passed'):
                portal('approve', revision_id=r['id'], digest=r['approval_digest'])
                use_key(provider)  # the key in force when the evaluation starts
                res = portal('evaluate', revision_id=r['id'], phase_id=PHASE)
                case.update(batch_id=res['batch_id'], public_test_score=test.get('score')); log('evaluating', case=name, public_test=test.get('score'))
                break
            # Only a terminal revision status is a failure; public_test.passed is false until the test finishes.
            if r['status'] in ('failed', 'rejected', 'error', 'invalid'):
                case.update(done=True, result='public_test_failed', status=r['status'], error=r.get('error'))
                log('failed', case=name, status=r['status'], error=r.get('error'),
                    jobs=[{k: j.get(k) for k in ('kind', 'status', 'code')} for j in portal('diagnostics', revision_id=r['id'])])
                break
            if time.time() > DEADLINE: raise TimeoutError('revision not ready: ' + r['status'] + ' ' + json.dumps(test)[:200])
            time.sleep(30)
        while case.get('batch_id') and not case.get('done'):
            b = batch_of(case['batch_id'])
            if b['status'] in ('scored', 'failed', 'cancelled'):
                case.update(done=True, result=b['status'], score=b.get('score'),
                            runs=[{k: x.get(k) for k in ('status', 'score', 'error')} for x in b['observer_runs']])
                log('finished', case=name, status=b['status'], score=b.get('score'), runs=case['runs']); break
            if time.time() > DEADLINE: raise TimeoutError('batch still ' + b['status'])
            time.sleep(30)
    except Exception as e:  # record and move on; the next run resumes from state
        log('error', case=name, error=str(e)[:400])
        if isinstance(e, TimeoutError): break
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False))

summary = {n: {k: c.get(k) for k in ('result', 'score', 'public_test_score', 'runs', 'error')} for n, c in state['cases'].items()}
(OUT / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False)); print(json.dumps(summary, ensure_ascii=False))
