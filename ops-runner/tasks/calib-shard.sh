#!/usr/bin/env bash
# Read-only on production: one shard of the practice-projects calibration study.
# ops-runner/calib/SHARD = "<scenario-slug> <first-index> <last-index>"
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
read -r slug first last < ops-runner/calib/SHARD
engine="$(tr -d '[:space:]' < ops-runner/calib/ENGINE_SHA)"
git fetch -q origin "$engine"
git worktree add -q /tmp/main "$engine"
export ENGINE_SHA="$engine"
row="$(sql "select s.id,s.slug,b.storage_path,b.digest from public.phase_scenarios ps join public.phases ph on ph.id=ps.phase_id join public.scenarios s on s.id=ps.scenario_id join private.observer_scenario_bundles b on b.scenario_id=s.id where ph.slug='practice-projects' and s.slug='$slug'" | python3 -c 'import json,sys; r=json.load(sys.stdin); assert len(r)==1; print(json.dumps(r[0]))')"
timeout 85m python ops-runner/analysis/calib_shard.py "$row" "$first" "$last"
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/calib && git commit -q -m "Calibration shard $slug $first-$last"
for i in 1 2 3 4 5; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && exit 0; sleep $((RANDOM % 10 + 2)); done
exit 1
