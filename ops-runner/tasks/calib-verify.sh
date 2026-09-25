#!/usr/bin/env bash
# Read-only: prepare one randomized practice-projects instance per scenario via prepare_bounded.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
engine="$(tr -d '[:space:]' < ops-runner/calib/ENGINE_SHA)"
git fetch -q origin "$engine"; git worktree add -q /tmp/main "$engine"
rows="$(sql "select s.slug,b.storage_path,p.profile from private.observer_scenario_calibration c join public.phases ph on ph.id=c.phase_id join public.scenarios s on s.id=c.scenario_id join private.observer_scenario_bundles b on b.scenario_id=s.id join private.observer_calibration_profiles p on p.id=c.profile_id where ph.slug='practice-projects' order by s.slug")"
PYTHONPATH=ops-runner/analysis timeout 85m python ops-runner/analysis/calib_verify.py "$rows" || echo "verify failed"
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/calib && git commit -q -m "Calibration verify results"
for i in 1 2 3 4 5; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && exit 0; sleep 5; done
