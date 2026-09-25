"""Merge calibration shards into the study file the calibration script would write,
then register the reviewed profiles for practice-projects via
scripts/configure-observer-calibration.py (dry run first, then --apply when APPLY=1).
Prints bounds and validation summaries only; no seeds or scenario data."""
import importlib.util, json, os, subprocess, sys
from pathlib import Path
from statistics import median
MAIN = Path('/tmp/main'); sys.path.insert(0, str(MAIN))
spec = importlib.util.spec_from_file_location('study', MAIN / 'scripts/calibrate-observer-scenarios.py')
study = importlib.util.module_from_spec(spec); sys.modules['study'] = study; spec.loader.exec_module(study)
from project_platform.scenario_instances import acceptance_reasons
from calib_shard import fetch

TRAIN, VALIDATE = 20, 10
phase = json.loads(sys.argv[1]); scenarios = json.loads(sys.argv[2]); installs = json.loads(sys.argv[3])
work = Path('/tmp/calib'); work.mkdir(exist_ok=True)
entries, report = [], {}
for sc in scenarios:
    shards = [json.loads(p.read_text()) for p in sorted(Path('ops-runner/results/calib', sc['slug']).glob('shard-*.json'))]
    assert shards and all(s['bundle_digest'] == sc['digest'] and s['engine_sha'] == os.environ['ENGINE_SHA'] for s in shards), sc['slug']
    rows = sorted((r for s in shards for r in s['rows']), key=lambda r: r['index'])
    assert [r['index'] for r in rows] == list(range(TRAIN + VALIDATE)), (sc['slug'], [r['index'] for r in rows])
    template = fetch(sc['storage_path'], sc['slug'])
    # Identical to calibrate-observer-scenarios.py main() after its sampling loop.
    profile = study.fit_profile(rows[:TRAIN], shards[0]['template_digest'])
    from project_platform.scenario_instances import directory_digest
    assert profile['template_digest'] == directory_digest(template)
    validation = rows[TRAIN:]
    for row in rows: row['rejections'] = acceptance_reasons(row['difficulty'], profile)
    scale = median(r['difficulty']['span'] for r in rows[:TRAIN])
    summary = {'training_seeds': TRAIN, 'validation_seeds': VALIDATE,
               'all_validation': study.summarize(validation, scale),
               'accepted_validation': study.summarize([r for r in validation if not r['rejections']], scale),
               'production_ready': False}
    result = {'summary': summary, 'candidate_profile': profile, 'samples': rows,
              'notice': 'Public experiment seeds; review on private competition templates before activation.'}
    path = work / f"{sc['slug']}-study.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    entries.append({'scenario_id': sc['id'], 'template': str(template), 'study': str(path), 'bundle_digest': sc['digest']})
    report[sc['slug']] = {'bounds': profile['bounds'], 'summary': summary}
    print(sc['slug'], json.dumps(report[sc['slug']]), flush=True)
manifest = {'phase_id': phase['id'], 'scenarios': entries,
            'runner_versions': {i['organization']: i['approved_sha'] for i in installs}}
(work / 'manifest.json').write_text(json.dumps(manifest))
out = {'report': report}
# The exact profiles configure-observer-calibration.py would register (it re-fits
# and applies the preregistered validation criteria); saved for the verify task.
cspec = importlib.util.spec_from_file_location('cfgcal', MAIN / 'scripts/configure-observer-calibration.py')
cfgcal = importlib.util.module_from_spec(cspec); cspec.loader.exec_module(cfgcal)
candidates = []
for sc, entry in zip(scenarios, entries):
    try:
        prof = cfgcal.reviewed_profile(entry['template'], entry['study'])
        candidates.append({'slug': sc['slug'], 'storage_path': sc['storage_path'], 'bundle_digest': sc['digest'], 'profile': prof})
        report[sc['slug']]['reviewed'] = {'ok': True, 'accepted_validation': prof['accepted_validation']}
    except Exception as error:
        report[sc['slug']]['reviewed'] = {'ok': False, 'error': str(error)}
    print(sc['slug'], 'reviewed', json.dumps(report[sc['slug']]['reviewed']), flush=True)
Path('ops-runner/results/calib/candidate-profiles.json').write_text(json.dumps(candidates, indent=1))
dry = subprocess.run([sys.executable, str(MAIN / 'scripts/configure-observer-calibration.py'), str(work / 'manifest.json')],
                     capture_output=True, text=True, cwd=MAIN)
out['dry_run'] = {'rc': dry.returncode, 'stdout': dry.stdout[-2000:], 'stderr': dry.stderr[-2000:]}
print('dry', json.dumps(out['dry_run']), flush=True)
if dry.returncode == 0 and os.environ.get('APPLY') == '1':
    app = subprocess.run([sys.executable, str(MAIN / 'scripts/configure-observer-calibration.py'), str(work / 'manifest.json'), '--apply'],
                         capture_output=True, text=True, cwd=MAIN)
    out['apply'] = {'rc': app.returncode, 'stdout': app.stdout[-2000:], 'stderr': app.stderr[-2000:]}
    print('apply', json.dumps(out['apply']), flush=True)
Path('ops-runner/results/calib/register.json').write_text(json.dumps(out, indent=1))
