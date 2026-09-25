#!/usr/bin/env bash
# Build the branch named in ops-runner/PREVIEW_BRANCH against the production
# backend (public anon key only), serve it locally on the runner and run the
# screenshot tour against it. Nothing is deployed.
set -euo pipefail
source ops-runner/lib.sh
load_project_keys
branch="$(tr -d '[:space:]' < ops-runner/PREVIEW_BRANCH)"
case "$branch" in ''|*..*|*' '*) echo "invalid preview branch" >&2; exit 2 ;; esac
git fetch -q --depth 1 origin "$branch"
git worktree add -q /tmp/preview FETCH_HEAD
echo "preview of $branch at $(git -C /tmp/preview rev-parse --short HEAD)"
npm ci --prefix /tmp/preview/web --no-audit --no-fund > /dev/null
( cd /tmp/preview/web && VITE_BASE_PATH=/survey26/platform/ VITE_SITE_URL=https://create.gosim.org/survey26/platform \
    VITE_SUPABASE_URL="$SUPABASE_URL" VITE_SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" npm run build > /dev/null )
( cd /tmp/preview/web && npx vite preview --host 127.0.0.1 --port 4173 --strictPort > /tmp/preview.log 2>&1 & )
for _ in $(seq 1 30); do curl -sf http://127.0.0.1:4173/survey26/platform/ > /dev/null && break; sleep 1; done
python -m pip install -q playwright==1.55.0
python -m playwright install --with-deps chromium > /dev/null
UX_BASE=http://127.0.0.1:4173/survey26/platform UX_LABEL="preview-${branch//\//-}" python ops-runner/ux_tour.py
git config user.name "ops-runner"
git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results
git commit -q -m "Preview tour screenshots for $branch"
git push -q origin HEAD:claude/ops-runner
