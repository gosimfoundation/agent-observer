"""Prepare one randomized instance per practice-projects scenario through the
engine's real path (project_platform.scenario_job.prepare_bounded with the
registered profile and a fresh random seed). Prints timings and difficulty vs
bounds only; the seed and scenario data are never printed or stored."""
import json, os, secrets, sys, time
from pathlib import Path
sys.path.insert(0, '/tmp/main')
from project_platform.scenario_job import prepare_bounded
from project_platform.scenario_instances import calibrated_score, POLICIES
from calib_shard import fetch

rows = json.loads(sys.argv[1]); out = {'cpus': os.cpu_count(), 'results': {}}
for row in rows:
    template = fetch(row['storage_path'], row['slug']); profile = row['profile']
    t0 = time.time()
    try:
        _, record = prepare_bounded(template, Path('/tmp/inst-' + row['slug']), seed=secrets.token_hex(32),
                                    profile=profile, max_candidates=32)
    except Exception as error:
        out['results'][row['slug']] = {'ok': False, 'error': str(error), 'seconds': round(time.time() - t0, 1)}
        print(row['slug'], out['results'][row['slug']], flush=True); continue
    d = record['difficulty']
    values = {'span': d['span'], 'open_fraction': d['open_fraction'],
              **{p: calibrated_score(d['policies'][p]['score'], d) for p in POLICIES}}
    out['results'][row['slug']] = {
        'ok': True, 'seconds': round(time.time() - t0, 1), 'candidate': record['candidate'],
        'rejected_candidates': [r['reasons'] for r in record['rejected_candidates']],
        'values_vs_bounds': {k: {'value': v, 'bounds': profile['bounds'][k],
                                 'inside': profile['bounds'][k][0] <= v <= profile['bounds'][k][1]} for k, v in values.items()},
        'template_digest_matches': record['template_digest'] == profile['template_digest']}
    print(row['slug'], json.dumps(out['results'][row['slug']]), flush=True)
Path('ops-runner/results/calib/verify.json').write_text(json.dumps(out, indent=1))
