#!/usr/bin/env bash
# Read-only: organizer-owned scored runs on the public practice scenarios (dev-reference, demo-week),
# as candidates for the home-page demo replay. Only teams that are hidden test teams, carry the
# platform test marker or contain an excluded (organizer) account are listed; participant runs never
# appear. Prints ids, team names, scores and file metadata only.
set -euo pipefail
source ops-runner/lib.sh
mkdir -p ops-runner/results/home-demo
# sha256 of decisions.csv from the official baseline (starter_kit/agent/minimal_agent.py) on dev-reference.
BASELINE_SHA=cc27367396cb76b68728e271446e23e9015bafe48c1036662c9a3683291cf0ab
sql "
with excluded as (
  select jsonb_array_elements_text(value) as id from public.site_settings where key='excluded_accounts'
), organizer_teams as (
  select t.id, t.name, t.is_hidden,
    bool_or(coalesce(u.raw_user_meta_data->>'observer_platform_e2e','')='true') as test_marker,
    bool_or(p.id::text in (select id from excluded)) as excluded_member
  from public.teams t join public.profiles p on p.team_id=t.id join auth.users u on u.id=p.id
  group by t.id
  having t.is_hidden or bool_or(coalesce(u.raw_user_meta_data->>'observer_platform_e2e','')='true') or bool_or(p.id::text in (select id from excluded))
)
select s.id as submission_id, e.id as evaluation_id, ot.name as team, ot.is_hidden, ot.test_marker, ot.excluded_member,
  s.kind, s.title, s.original_filename, s.sha256, (s.sha256='${BASELINE_SHA}') as baseline_sha_match,
  ph.slug as phase, sc.slug as scenario, e.score, e.summary->>'n_actions' as n_actions, e.summary->>'termination_reason' as termination,
  e.replay_path <> '' as has_replay, e.report_path <> '' as has_report, e.finished_at::text as finished
from public.evaluations e
join public.submissions s on s.id=e.submission_id
join organizer_teams ot on ot.id=s.team_id
join public.phases ph on ph.id=s.phase_id
join public.scenarios sc on sc.id=e.scenario_id
where e.status='scored' and sc.slug in ('dev-reference','demo-week')
order by (s.sha256='${BASELINE_SHA}') desc, sc.slug, e.finished_at desc
limit 60
" > ops-runner/results/home-demo/candidates.json
python3 - <<'PY'
import json
rows=json.load(open('ops-runner/results/home-demo/candidates.json'))
print(len(rows),'organizer-owned scored runs')
for r in rows:
    print(r['submission_id'],r['evaluation_id'],'|',r['team'],'|',r['kind'],r['original_filename'],'| baseline_sha=',r['baseline_sha_match'],'|',r['phase'],r['scenario'],'| score',r['score'],'| actions',r['n_actions'],'| replay',r['has_replay'],'|',r['finished'])
PY
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/home-demo && git commit -q -m "Home demo: organizer baseline candidates"
for i in 1 2 3 4 5; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && exit 0; sleep 5; done
