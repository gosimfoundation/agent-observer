#!/usr/bin/env bash
# Read-only: how long does preparing one randomized formal instance take here?
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
git fetch -q --depth 1 origin main
git worktree add -q /tmp/main FETCH_HEAD
python -m pip install -q -r /tmp/main/requirements.txt 2>/dev/null || true
rows="$(sql "select s.slug, b.storage_path, p.profile from public.phase_scenarios ps join public.phases ph on ph.id=ps.phase_id join public.scenarios s on s.id=ps.scenario_id join private.observer_scenario_bundles b on b.scenario_id=s.id join private.observer_scenario_calibration c on c.phase_id=ph.id and c.scenario_id=s.id join private.observer_calibration_profiles p on p.id=c.profile_id where ph.slug='online' order by s.slug")"
CANDIDATES=4 timeout 80m python ops-runner/analysis/instance_timing.py "$rows" || true
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/instance-timing.json 2>/dev/null && git commit -q -m "Instance preparation timing" && git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner || true
