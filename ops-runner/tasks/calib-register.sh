#!/usr/bin/env bash
# Register the practice-projects calibration profiles (APPLY in ops-runner/calib/APPLY),
# then report the phase's calibration rows. Touches only practice-projects.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
engine="$(tr -d '[:space:]' < ops-runner/calib/ENGINE_SHA)"
git fetch -q origin "$engine"; git worktree add -q /tmp/main "$engine"
export ENGINE_SHA="$engine" APPLY="$(tr -d '[:space:]' < ops-runner/calib/APPLY)"
phase="$(sql "select id from public.phases where slug='practice-projects'" | python3 -c 'import json,sys; r=json.load(sys.stdin); assert len(r)==1; print(json.dumps(r[0]))')"
scen="$(sql "select s.id,s.slug,b.storage_path,b.digest from public.phase_scenarios ps join public.phases ph on ph.id=ps.phase_id join public.scenarios s on s.id=ps.scenario_id join private.observer_scenario_bundles b on b.scenario_id=s.id where ph.slug='practice-projects' order by s.slug")"
inst="$(sql "select organization,approved_sha from private.observer_installations order by 1")"
PYTHONPATH=ops-runner/analysis python ops-runner/analysis/calib_register.py "$phase" "$scen" "$inst" || echo "register script failed"
sql "select s.slug,c.profile_id,p.bundle_digest,p.profile->'bounds' as bounds,p.profile->'accepted_validation' as validation from private.observer_scenario_calibration c join public.phases ph on ph.id=c.phase_id join public.scenarios s on s.id=c.scenario_id join private.observer_calibration_profiles p on p.id=c.profile_id where ph.slug='practice-projects'" > ops-runner/results/calib/registered.json
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/calib && git commit -q -m "Calibration register results"
for i in 1 2 3 4 5; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && exit 0; sleep 5; done
