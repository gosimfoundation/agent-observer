#!/usr/bin/env bash
# Read-only: phase settings for the announcement, then re-shoot the footer fact.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
mkdir -p ops-runner/results/facts
sql "select p.slug, s.projects_enabled, s.local_sessions_enabled, s.runtime_seconds, s.daily_batches from public.observer_phase_settings s join public.phases p on p.id = s.phase_id where p.slug in ('online','practice','practice-projects')" > ops-runner/results/facts/phase-settings.json
cat ops-runner/results/facts/phase-settings.json
curl -s https://api.github.com/repos/gosimfoundation/hackathon-survey26/releases/latest | python3 -c "import json,sys; d=json.load(sys.stdin); print('latest release', d.get('tag_name'), d.get('published_at'))"
python -m pip install -q playwright==1.55.0
python -m playwright install --with-deps chromium > /dev/null
python ops-runner/footer_fact.py
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results
git commit -q -m "Phase settings and footer re-shoot"
for i in 1 2 3 4; do git pull -q --rebase origin claude/ops-runner && git push -q origin HEAD:claude/ops-runner && break; sleep 5; done
