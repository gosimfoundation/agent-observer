#!/usr/bin/env bash
# Read-only probe: which secrets are configured, which hosts are reachable, and
# whether the model keys are accepted. Prints status codes and set/missing only.
set -uo pipefail

for name in SUPABASE_URL SUPABASE_ANON_KEY SUPABASE_SERVICE_ROLE_KEY SUPABASE_ACCESS_TOKEN KIMI_API_KEY GLM_API_KEY; do
  if [ -n "${!name:-}" ]; then echo "secret $name: set"; else echo "secret $name: missing"; fi
done

code() { curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$@" || true; }

echo "reach create.gosim.org: $(code https://create.gosim.org/survey26/platform/)"
echo "reach supabase project: $(code "https://${SUPABASE_PROJECT_REF}.supabase.co/auth/v1/health")"
echo "reach api.supabase.com: $(code https://api.supabase.com/v1/projects)"

key="${SUPABASE_SERVICE_ROLE_KEY:-${SUPABASE_ANON_KEY:-}}"
if [ -n "$key" ] && [ -n "${SUPABASE_URL:-}" ]; then
  echo -n "rpc current_competition: "
  curl -s --max-time 20 "$SUPABASE_URL/rest/v1/rpc/current_competition" \
    -H "apikey: $key" -H "Authorization: Bearer $key" -H "Content-Type: application/json" -d '{}' | head -c 300
  echo
fi

if [ -n "${SUPABASE_ACCESS_TOKEN:-}" ]; then
  curl -s --max-time 20 "https://api.supabase.com/v1/projects/${SUPABASE_PROJECT_REF}" \
    -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" > /tmp/project.json || true
  python3 - <<'PY'
import json
try:
    d = json.load(open('/tmp/project.json'))
except Exception as exc:
    print('management project: unreadable', type(exc).__name__)
else:
    print('management project:', {k: d.get(k) for k in ('name', 'region', 'status', 'organization_id')})
PY
fi

if [ -n "${KIMI_API_KEY:-}" ]; then
  for host in api.moonshot.cn api.moonshot.ai; do
    echo "kimi $host /v1/models: $(code "https://$host/v1/models" -H "Authorization: Bearer $KIMI_API_KEY")"
  done
fi

if [ -n "${GLM_API_KEY:-}" ]; then
  body='{"model":"glm-4.5-flash","messages":[{"role":"user","content":"ping"}],"max_tokens":1}'
  for url in https://open.bigmodel.cn/api/paas/v4 https://open.bigmodel.cn/api/coding/paas/v4 \
             https://api.z.ai/api/paas/v4 https://api.z.ai/api/coding/paas/v4; do
    echo "glm $url: $(code "$url/chat/completions" -H "Authorization: Bearer $GLM_API_KEY" \
      -H "Content-Type: application/json" -d "$body")"
  done
fi
