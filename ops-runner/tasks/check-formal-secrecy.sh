#!/usr/bin/env bash
# Read-only: is any formal scenario material reachable before the competition opens?
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
anon() { curl -s --max-time 30 "$SUPABASE_URL$1" -H "apikey: $SUPABASE_ANON_KEY" -H "Authorization: Bearer $SUPABASE_ANON_KEY"; }
echo "online phase (as anonymous visitor):"; anon "/rest/v1/phases?slug=eq.online&select=slug,starts_at,is_active" ; echo
echo "phase_scenarios visible to visitors:"; anon "/rest/v1/phase_scenarios?select=phase_id,scenario_id" | head -c 600; echo
echo "scenario rows visible to visitors:"; anon "/rest/v1/scenarios?select=slug,is_active" | head -c 600; echo
echo "storage buckets:"; sql "select id, public from storage.buckets order by id"
echo "formal scenario storage (private bundles):"; sql "select p.slug phase, s.slug scenario, b.storage_path is not null as has_private_bundle from public.phase_scenarios ps join public.phases p on p.id=ps.phase_id join public.scenarios s on s.id=ps.scenario_id left join private.observer_scenario_bundles b on b.scenario_id=s.id where p.slug='online'"
echo "public scenario files in storage buckets named like the formal scenarios:"; sql "select bucket_id, count(*) from storage.objects o join storage.buckets bk on bk.id=o.bucket_id where bk.public and (o.name ilike '%eval-a%' or o.name ilike '%eval-b%') group by 1"
