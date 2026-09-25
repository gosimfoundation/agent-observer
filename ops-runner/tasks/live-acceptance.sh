#!/usr/bin/env bash
# Live acceptance as the hidden acceptance team (see ops-runner/acceptance/live.py).
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
git fetch -q --depth 1 origin main
git worktree add -q /tmp/main FETCH_HEAD
python ops-runner/acceptance/live.py || true
git config user.name "ops-runner"; git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/acceptance
git commit -q -m "Live acceptance progress" || true
git pull -q --rebase origin claude/ops-runner || true
git push -q origin HEAD:claude/ops-runner
