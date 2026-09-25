#!/usr/bin/env bash
# Read-only: state of practice-projects scenarios, bundles, calibration and batches.
set -euo pipefail
source ops-runner/lib.sh
out=ops-runner/results/calib/probe.json
{
echo '{"phase":'; sql "select p.id,p.slug,p.is_active,p.counts_for_final,s.* from public.phases p left join public.observer_phase_settings s on s.phase_id=p.id where p.slug in ('practice-projects','online')"
echo ',"scenarios":'; sql "select s.id,s.slug,s.global_wallclock_seconds,b.storage_path,b.digest from public.phase_scenarios ps join public.phases ph on ph.id=ps.phase_id join public.scenarios s on s.id=ps.scenario_id left join private.observer_scenario_bundles b on b.scenario_id=s.id where ph.slug='practice-projects' order by s.slug"
echo ',"batches":'; sql "select b.purpose,b.status,count(*) from public.observer_batches b join public.phases p on p.id=b.phase_id where p.slug='practice-projects' group by 1,2"
echo ',"submissions":'; sql "select count(*) from public.submissions s join public.phases p on p.id=s.phase_id where p.slug='practice-projects'"
echo ',"calibration":'; sql "select p.slug,c.scenario_id,c.profile_id,cp.bundle_digest,cp.profile - 'accepted_validation' as profile from private.observer_scenario_calibration c join public.phases p on p.id=c.phase_id join private.observer_calibration_profiles cp on cp.id=c.profile_id where p.slug in ('practice-projects','online')"
echo ',"installations":'; sql "select organization,approved_sha,enabled from private.observer_installations order by 1"
echo ',"triggers":'; sql "select tgname,pg_get_triggerdef(t.oid) from pg_trigger t where tgname like 'observer_%calib%' or tgname like 'observer_allocate%'"
echo ',"alloc_fn":'; sql "select pg_get_functiondef('private.observer_allocate_instance'::regproc) as def, pg_get_functiondef('private.observer_configure_calibration'::regproc) as def2"
echo '}'
} > "$out"
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add "$out" && git commit -q -m "calib probe results [skip ci]" && git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner || true
