#!/usr/bin/env bash
# Apply pending migrations from a ref, then plan (or with PRACTICE_APPLY=1 open)
# the Playground complete-project board.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
ref="$(tr -d '[:space:]' < ops-runner/PRACTICE_REF)"; apply="$(tr -d '[:space:]' < ops-runner/PRACTICE_APPLY)"
git fetch -q --depth 1 origin "$ref"
git worktree add -q /tmp/pp FETCH_HEAD
cd /tmp/pp
echo "ref $ref at $(git rev-parse --short HEAD)"
python scripts/deploy-observer-backend.py --apply
if [ "$apply" = 1 ]; then python scripts/configure-observer-practice-projects.py --apply
else python scripts/configure-observer-practice-projects.py; fi
