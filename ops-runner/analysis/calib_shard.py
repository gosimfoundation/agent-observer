"""One shard of scripts/calibrate-observer-scenarios.py for a practice-projects scenario.

Runs the study's own sample() for a contiguous index range on the scenario's
registered private bundle (public experiment seeds only) and writes the rows.
Merging all shards reproduces the study output exactly (same seeds, same code).
"""
import importlib.util, io, json, os, sys, time, zipfile, urllib.request
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
MAIN = Path('/tmp/main'); sys.path.insert(0, str(MAIN))
spec = importlib.util.spec_from_file_location('study', MAIN / 'scripts/calibrate-observer-scenarios.py')
study = importlib.util.module_from_spec(spec); sys.modules['study'] = study; spec.loader.exec_module(study)
from project_platform.scenario_instances import directory_digest

def fetch(storage_path, slug):
    base = os.environ['SUPABASE_URL']; key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    req = urllib.request.Request(base + '/storage/v1/object/authenticated/observer-scenarios/' + storage_path,
                                 headers={'apikey': key, 'Authorization': 'Bearer ' + key})
    with urllib.request.urlopen(req, timeout=120) as r: raw = r.read()
    template = Path('/tmp/tpl-' + slug); template.mkdir()
    zipfile.ZipFile(io.BytesIO(raw)).extractall(template)
    return template

if __name__ == '__main__':
    row = json.loads(sys.argv[1]); first, last = int(sys.argv[2]), int(sys.argv[3])
    template = fetch(row['storage_path'], row['slug'])
    t0 = time.time(); rows = []
    with ProcessPoolExecutor(max_workers=int(os.environ.get('WORKERS', '4'))) as pool:
        for r in pool.map(study.sample, ((template, i) for i in range(first, last + 1))):
            rows.append(r); print(row['slug'], 'sample', r['index'], round(time.time() - t0, 1), 's', flush=True)
    out = Path(f"ops-runner/results/calib/{row['slug']}/shard-{first:02}-{last:02}.json"); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'scenario_id': row['id'], 'slug': row['slug'], 'bundle_digest': row['digest'],
                               'template_digest': directory_digest(template), 'engine_sha': os.environ.get('ENGINE_SHA'),
                               'wall_s': round(time.time() - t0, 1), 'cpus': os.cpu_count(), 'rows': rows}, sort_keys=True))
