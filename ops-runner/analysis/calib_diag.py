"""Diagnose invalid_calibration_span: per-policy panel scores on the template and on
public experiment seed 0 for each practice-projects scenario. Scores only."""
import hashlib, json, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
sys.path.insert(0, '/tmp/main')
from project_platform.scenario_instances import benchmark_policy, generate_candidate, POLICIES, HOLDOUT_POLICY
from calib_shard import fetch

def run(args):
    path, name = args; t = time.time()
    try: r = benchmark_policy(Path(path), name)
    except Exception as e: r = {'error': repr(e)}
    r['seconds'] = round(time.time() - t, 1); return r

out = {}
for row in json.loads(sys.argv[1]):
    template = fetch(row['storage_path'], row['slug'])
    cfg = {n: json.loads((template / 'config' / n).read_text()) for n in ('scenario_config.json', 'calendar_config.json') if (template / 'config' / n).exists()}
    seed = hashlib.sha256(b"public-calibration-experiment-v1/0").hexdigest()
    inst = Path('/tmp/diag-' + row['slug']); generate_candidate(template, inst, seed=seed, candidate=0)
    names = (*POLICIES, HOLDOUT_POLICY, 'wait')
    jobs = [(str(p), n) for p in (template, inst) for n in names]
    with ProcessPoolExecutor(4) as pool: res = list(pool.map(run, jobs))
    out[row['slug']] = {'config_keys': {k: sorted(v) for k, v in cfg.items()},
                        'calendar': {k: v for k, v in cfg.get('calendar_config.json', {}).items() if not isinstance(v, (list, dict))},
                        'template': dict(zip(names, res[:len(names)])), 'seed0': dict(zip(names, res[len(names):]))}
    print(row['slug'], json.dumps(out[row['slug']]), flush=True)
Path('ops-runner/results/calib/diag.json').write_text(json.dumps(out, indent=1))
