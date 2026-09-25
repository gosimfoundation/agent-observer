#!/usr/bin/env bash
# Hide the six verified platform test teams (exact names) from participant lists
# and boards, take their members off the player wall and add them to the
# excluded accounts. Reversible: set teams.is_hidden=false again.
set -euo pipefail
source ops-runner/lib.sh
names="'GLM Flash 验收 A 0924','GLM Flash 验收 B 0924','GLM Flash 验收 C 0924','acceptance-w04-验收测试队-30f6','Acceptance W02 (platform test)','ACC-RUST03 acceptance (not for board)'"
sql "
begin;
update public.teams set is_hidden=true where name in ($names);
update public.profiles set show_on_wall=false where team_id in (select id from public.teams where name in ($names));
insert into public.site_settings(key,value)
  select 'excluded_accounts', coalesce(jsonb_agg(p.id::text),'[]'::jsonb)
  from public.profiles p join public.teams t on t.id=p.team_id where t.name in ($names)
on conflict(key) do update set value=(
  select jsonb_agg(distinct x) from jsonb_array_elements_text(public.site_settings.value || excluded.value) as x);
commit;
" > /dev/null
sql "select t.name, t.is_hidden, count(p.id) as members, bool_and(not p.show_on_wall) as off_wall
     from public.teams t left join public.profiles p on p.team_id=t.id
     where t.name in ($names) group by t.name, t.is_hidden order by t.name"
echo
sql "select count(*) as visible_test_teams from public.team_directory() where name ~* '(accept|验收|platform test|not for board)'"
