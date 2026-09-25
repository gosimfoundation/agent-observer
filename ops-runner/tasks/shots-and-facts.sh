#!/usr/bin/env bash
# Live screenshots (full tour + footer fact popup) and the read-only phase facts the announcement needs.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
mkdir -p ops-runner/results/facts
sql "select slug, name_zh, starts_at, ends_at, daily_limit, counts_for_final, is_active, allow_results, allow_agents from public.phases order by sort_order, starts_at" > ops-runner/results/facts/phases.json
sql "select m.mode, p.slug from private.observer_site_mode m left join public.phases p on p.id = m.phase_id" > ops-runner/results/facts/site-mode.json
sql "select count(*) as saved_team_models from private.observer_team_models" > ops-runner/results/facts/saved-keys.json 2>/dev/null || echo '[]' > ops-runner/results/facts/saved-keys.json
cat ops-runner/results/facts/*.json
python -m pip install -q playwright==1.55.0
python -m playwright install --with-deps chromium > /dev/null
python ops-runner/footer_fact.py
UX_LABEL=ux-tour-practice python ops-runner/ux_tour.py
git config user.name "ops-runner"
git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results
git commit -q -m "Live screenshots and phase facts"
for i in 1 2 3 4; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && break; sleep 5; done
