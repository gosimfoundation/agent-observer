#!/usr/bin/env bash
# Smoke acceptance (~5-10 min) with its own hidden smoke team, account, private
# scenario and internal phase (see ops-runner/acceptance/smoke.py). Never uses
# the full acceptance team or phase. Push with "[parallel]" in the message.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
git fetch -q --depth 1 origin "${SMOKE_MAIN_REF:-main}"
git worktree add -q /tmp/main FETCH_HEAD
status=0
python ops-runner/acceptance/smoke.py || status=$?
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/smoke
git commit -q -m "Smoke acceptance result" || true
git pull -q --rebase origin claude/ops-runner || true
git push -q origin HEAD:claude/ops-runner || true
exit $status
