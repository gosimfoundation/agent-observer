#!/usr/bin/env bash
# Deploy the Observer backend from a reviewed ref named in ops-runner/DEPLOY:
#   ref=<branch>          what to deploy (fetched fresh; nothing else is used)
#   apply=0|1             0 = dry run (list pending migrations only)
#   functions=<names>     Edge functions to deploy when apply=1, in order
# Migrations go first (hash-recorded; the script rolls back if any legacy public
# table changes), then the functions. Nothing prints a credential.
set -euo pipefail
source ops-runner/lib.sh
conf() { sed -n "s/^$1=//p" ops-runner/DEPLOY | tr -d '\r'; }
ref="$(conf ref)"; apply="$(conf apply)"; functions="$(conf functions)"
case "$ref" in ''|*..*|*' '*|-*) echo "invalid ref" >&2; exit 2 ;; esac
case "$apply" in 0|1) ;; *) echo "apply must be 0 or 1" >&2; exit 2 ;; esac
for f in $functions; do
  case "$f" in observer-model|observer-portal|observer-session|observer-job|observer-dispatch|leaderboard) ;;
    *) echo "unknown function $f" >&2; exit 2 ;; esac
done
git fetch -q --depth 1 origin "$ref"
git worktree add -q /tmp/deploy FETCH_HEAD
cd /tmp/deploy
echo "ref $ref at $(git rev-parse HEAD)"
python scripts/deploy-observer-backend.py
if [ "$apply" = 1 ]; then
  python scripts/deploy-observer-backend.py --apply
  for f in $functions; do
    npx -y supabase@2 functions deploy "$f" --project-ref "$SUPABASE_PROJECT_REF" --use-api
  done
fi
echo "recent migrations:"
sql "select version, left(digest, 12) as digest, applied_at from private.observer_migrations order by version desc limit 6"
echo "functions:"
curl -sf --max-time 30 "https://api.supabase.com/v1/projects/${SUPABASE_PROJECT_REF}/functions" \
  -H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}" |
  python3 -c 'import json,sys; [print(f["slug"], "v"+str(f.get("version")), f.get("status"), f.get("updated_at")) for f in sorted(json.load(sys.stdin), key=lambda f: f["slug"])]'
