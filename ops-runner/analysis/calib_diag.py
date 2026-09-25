"""Diagnose invalid_calibration_span: score breakdown of the gain_rate panel policy
and of the all-wait control on each practice-projects template. Scores only."""
import json, sys
from pathlib import Path
sys.path.insert(0, '/tmp/main')
import project_platform.scenario_instances as si
from calib_shard import fetch

captured = {}
class Capture(si.ChallengeWorkflow):
    def run(self, decide):
        result = super().run(decide); captured['report'] = result['score_report']; return result
    def __init__(self, *a, **k):
        super().__init__(*a, **k); orig = self.scorer.finalize
        def fin(*x, **y):
            r = orig(*x, **y); captured['report'] = r; return r
        self.scorer.finalize = fin
si.ChallengeWorkflow = Capture

def trim(report):
    s = report.get('score', {})
    return {'score': s, 'completion': {k: (len(v) if isinstance(v, list) else v) for k, v in report.get('completion', {}).items()},
            'other_keys': sorted(report)}

out = {}
for row in json.loads(sys.argv[1]):
    template = fetch(row['storage_path'], row['slug']); out[row['slug']] = {}
    for policy in ('gain_rate', 'wait'):
        captured.clear(); si.benchmark_policy(template, policy)
        out[row['slug']][policy] = trim(captured['report'])
    out[row['slug']]['scoring_contract'] = json.loads((template / 'config/scenario_config.json').read_text()).get('contract_semantics')
    print(row['slug'], json.dumps(out[row['slug']], default=str)[:6000], flush=True)
Path('ops-runner/results/calib/diag2.json').write_text(json.dumps(out, indent=1, default=str))
