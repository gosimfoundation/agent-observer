#!/usr/bin/env bash
# Apply pending migrations from main, then give the hidden acceptance team its
# own phase on the formal scenarios (same seeds/calibration as `online`).
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
git fetch -q --depth 1 origin main
git worktree add -q /tmp/main FETCH_HEAD
cd /tmp/main
echo "main at $(git rev-parse --short HEAD)"
python scripts/deploy-observer-backend.py --apply
team="$(sql "select id from public.teams where is_hidden and name='Observer platform acceptance test'" | python3 -c 'import json,sys; r=json.load(sys.stdin); assert len(r)==1, r; print(r[0]["id"])')"
python scripts/configure-observer-acceptance.py --team-id "$team" --same-as online --apply | grep -v "^-- "
