"""Time private instance preparation (generate + difficulty check) on a runner.

Prints only timings, pass/fail and failed bound names; no scenario data.
"""
import io, json, os, secrets, sys, time, zipfile, urllib.request
from pathlib import Path
sys.path.insert(0, '/tmp/main')
from project_platform.scenario_instances import generate_candidate, measure_difficulty, acceptance_reasons, directory_digest

BASE = os.environ['SUPABASE_URL']; SERVICE = os.environ['SUPABASE_SERVICE_ROLE_KEY']
def get(path):
    req = urllib.request.Request(BASE + path, headers={'apikey': SERVICE, 'Authorization': 'Bearer ' + SERVICE})
    with urllib.request.urlopen(req, timeout=120) as r: return r.read()

rows = json.loads(sys.argv[1])
per = int(os.environ.get('CANDIDATES', '4'))
out = {}
for row in rows:
    raw = get('/storage/v1/object/authenticated/observer-scenarios/' + row['storage_path'])
    template = Path('/tmp/tpl-' + row['slug']); template.mkdir()
    zipfile.ZipFile(io.BytesIO(raw)).extractall(template)
    profile = row['profile']
    assert profile['template_digest'] == directory_digest(template), 'template digest differs'
    seed = secrets.token_hex(32); results = []
    for i in range(per):
        t0 = time.time(); dest = Path(f'/tmp/cand-{row["slug"]}-{i}')
        generate_candidate(template, dest, seed=seed, candidate=i); t1 = time.time()
        diff = measure_difficulty(dest); t2 = time.time()
        reasons = acceptance_reasons(diff, profile)
        results.append({'generate_s': round(t1 - t0, 1), 'measure_s': round(t2 - t1, 1), 'ok': not reasons, 'failed_bounds': reasons})
        print(row['slug'], json.dumps(results[-1]), flush=True)
    out[row['slug']] = results
Path('ops-runner/results/instance-timing.json').write_text(json.dumps({'cpus': os.cpu_count(), 'results': out}, indent=1))
