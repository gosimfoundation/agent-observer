#!/usr/bin/env bash
# Read-only: list teams that look like platform test teams, with the reason.
# Prints team names, flags and member email domains only (never full emails).
set -euo pipefail
source ops-runner/lib.sh
sql "
with excluded as (
  select jsonb_array_elements_text(value) as id from public.site_settings where key='excluded_accounts'
), members as (
  select p.team_id,
    count(*) as members,
    bool_or(coalesce(u.raw_user_meta_data->>'observer_platform_e2e','')='true') as has_test_marker,
    bool_or(p.id::text in (select id from excluded)) as has_excluded_member,
    string_agg(distinct split_part(u.email,'@',2), ',') as email_domains
  from public.profiles p join auth.users u on u.id=p.id
  where p.team_id is not null group by p.team_id
)
select t.id, t.name, t.is_hidden, t.created_at::date as created, m.members, m.has_test_marker,
  m.has_excluded_member, m.email_domains,
  (t.name ~* '(accept|platform test|not for board|e2e|lab|验收|test)') as name_match
from public.teams t left join members m on m.team_id=t.id
where t.name ~* '(accept|platform test|not for board|e2e|lab|验收|test)'
   or coalesce(m.has_test_marker,false) or coalesce(m.has_excluded_member,false)
order by t.created_at
" | python3 -c "
import json,sys
rows=json.load(sys.stdin)
print(len(rows),'candidate teams')
for r in rows:
    print(r['id'][:8], '|', r['name'], '| hidden=',r['is_hidden'], '| members=',r['members'], '| marker=',r['has_test_marker'],
          '| excluded=',r['has_excluded_member'], '| name_match=',r['name_match'], '| domains=',r['email_domains'], '|', r['created'])
"
