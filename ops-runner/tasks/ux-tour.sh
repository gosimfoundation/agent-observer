#!/usr/bin/env bash
# Screenshot tour of the live site; commits the results to this branch.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
python -m pip install -q playwright==1.55.0
python -m playwright install --with-deps chromium > /dev/null
python ops-runner/ux_tour.py
git config user.name "ops-runner"
git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results
git commit -q -m "UX tour screenshots"
git push -q origin HEAD:claude/ops-runner
