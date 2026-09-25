#!/usr/bin/env bash
# Read-only: why no organizer baseline candidate was found. Aggregate counts only, plus the
# organizer-owned rows (hidden/test/excluded teams). No participant team names or files.
set -euo pipefail
source ops-runner/lib.sh
mkdir -p ops-runner/results/home-demo
{
echo '## scenarios with scored evaluations'
sql "select sc.slug, sc.tiles_public, sc.weather_public, count(*) filter (where e.status='scored') as scored, max((e.summary->>'n_actions')::int) as max_actions from public.evaluations e join public.scenarios sc on sc.id=e.scenario_id group by 1,2,3 order by 1"
echo '## organizer teams (hidden, test marker or excluded member)'
sql "
with excluded as (select jsonb_array_elements_text(value) as id from public.site_settings where key='excluded_accounts')
select t.name, t.is_hidden,
  bool_or(coalesce(u.raw_user_meta_data->>'observer_platform_e2e','')='true') as marker,
  bool_or(p.id::text in (select id from excluded)) as excluded_member,
  (select count(*) from public.submissions s where s.team_id=t.id) as submissions,
  (select count(*) from public.submissions s join public.evaluations e on e.submission_id=s.id where s.team_id=t.id and e.status='scored') as scored_evals
from public.teams t left join public.profiles p on p.team_id=t.id left join auth.users u on u.id=p.id
group by t.id having t.is_hidden or bool_or(coalesce(u.raw_user_meta_data->>'observer_platform_e2e','')='true') or bool_or(p.id::text in (select id from excluded))
order by t.created_at"
echo '## scored evaluations owned by organizer teams (any scenario)'
sql "
with excluded as (select jsonb_array_elements_text(value) as id from public.site_settings where key='excluded_accounts'),
org as (select t.id, t.name from public.teams t left join public.profiles p on p.team_id=t.id left join auth.users u on u.id=p.id
  group by t.id having t.is_hidden or bool_or(coalesce(u.raw_user_meta_data->>'observer_platform_e2e','')='true') or bool_or(p.id::text in (select id from excluded)))
select s.id as sub, e.id as ev, org.name as team, s.kind, s.original_filename, s.sha256='cc27367396cb76b68728e271446e23e9015bafe48c1036662c9a3683291cf0ab' as baseline_sha,
  ph.slug as phase, sc.slug as scenario, round(e.score::numeric,3) as score, e.summary->>'n_actions' as actions, e.replay_path<>'' as replay, e.finished_at::date as day
from public.evaluations e join public.submissions s on s.id=e.submission_id join org on org.id=s.team_id
join public.phases ph on ph.id=s.phase_id join public.scenarios sc on sc.id=e.scenario_id
where e.status='scored' order by e.finished_at desc limit 80"
echo '## submission 223 (the one the owner reported): organizer-owned?'
sql "
with excluded as (select jsonb_array_elements_text(value) as id from public.site_settings where key='excluded_accounts')
select s.id, t.is_hidden, bool_or(p.id::text in (select id from excluded)) as excluded_member, s.kind, sc.slug, e.summary->>'n_actions' as actions
from public.submissions s join public.teams t on t.id=s.team_id left join public.profiles p on p.team_id=t.id
join public.evaluations e on e.submission_id=s.id join public.scenarios sc on sc.id=e.scenario_id where s.id=223 group by s.id,t.is_hidden,s.kind,sc.slug,e.summary"
} > ops-runner/results/home-demo/diag.txt
cat ops-runner/results/home-demo/diag.txt
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/home-demo && git commit -q -m "Home demo: candidate diagnostics"
for i in 1 2 3 4 5; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && exit 0; sleep 5; done
