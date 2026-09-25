#!/usr/bin/env bash
# Shared helpers for ops-runner tasks. Nothing here prints a credential.

# Exports SUPABASE_URL, SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY from the
# management API using SUPABASE_ACCESS_TOKEN; both keys are masked in the log.
load_project_keys() {
  export SUPABASE_URL="https://${SUPABASE_PROJECT_REF}.supabase.co"
  local keys
  keys="$(curl -sf --max-time 30 "https://api.supabase.com/v1/projects/${SUPABASE_PROJECT_REF}/api-keys" \
    -H "Authorization: Bearer ${SUPABASE_ACCESS_TOKEN}")" || { echo "cannot read project api keys" >&2; return 1; }
  local anon service
  anon="$(python3 -c 'import json,sys; print(next(k["api_key"] for k in json.load(sys.stdin) if k.get("name")=="anon"))' <<<"$keys")"
  service="$(python3 -c 'import json,sys; print(next(k["api_key"] for k in json.load(sys.stdin) if k.get("name")=="service_role"))' <<<"$keys")"
  echo "::add-mask::$anon"
  echo "::add-mask::$service"
  export SUPABASE_ANON_KEY="$anon" SUPABASE_SERVICE_ROLE_KEY="$service"
}

# Runs one read-only SQL statement through the management API and prints JSON rows.
sql() {
  python3 - "$1" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(
    "https://api.supabase.com/v1/projects/" + os.environ["SUPABASE_PROJECT_REF"] + "/database/query",
    data=json.dumps({"query": sys.argv[1]}).encode(),
    headers={"Authorization": "Bearer " + os.environ["SUPABASE_ACCESS_TOKEN"], "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as response:
    print(json.dumps(json.load(response), ensure_ascii=False, default=str))
PY
}
