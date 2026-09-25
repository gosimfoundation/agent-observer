#!/usr/bin/env bash
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
engine="$(tr -d '[:space:]' < ops-runner/calib/ENGINE_SHA)"
git fetch -q origin "$engine"; git worktree add -q /tmp/main "$engine"
rows="$(sql "select s.slug,b.storage_path from public.phase_scenarios ps join public.phases ph on ph.id=ps.phase_id join public.scenarios s on s.id=ps.scenario_id join private.observer_scenario_bundles b on b.scenario_id=s.id where ph.slug='practice-projects' order by s.slug")"
PYTHONPATH=ops-runner/analysis timeout 60m python ops-runner/analysis/calib_diag.py "$rows" || echo "diag failed"
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/calib && git commit -q -m "Calibration diag results"
for i in 1 2 3 4 5; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && exit 0; sleep 5; done
