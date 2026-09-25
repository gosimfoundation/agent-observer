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
  source ops-runner/lib.sh
  curl -s --max-time 20 "https://api.supabase.com/v1/projects/${SUPABASE_PROJECT_REF}" \
    -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" > /tmp/project.json || true
  org="$(python3 - <<'PY'
import json
try:
    d = json.load(open('/tmp/project.json'))
except Exception as exc:
    print('management project: unreadable', type(exc).__name__, file=__import__('sys').stderr)
else:
    print('management project:', {k: d.get(k) for k in ('name', 'region', 'status', 'organization_id')}, file=__import__('sys').stderr)
    print(d.get('organization_id') or '')
PY
)"
  if [ -n "$org" ]; then
    curl -s --max-time 20 "https://api.supabase.com/v1/organizations/$org" \
      -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" > /tmp/org.json || true
    python3 -c "import json; d=json.load(open('/tmp/org.json')); print('organization plan:', d.get('plan'), '| fields:', sorted(d))" || true
  fi
  if load_project_keys; then echo "project api keys: loaded (masked)"; fi
  for label_query in \
    "current_competition|select public.current_competition() as value" \
    "phases|select slug,starts_at,ends_at,is_active,counts_for_final from public.phases order by sort_order" \
    "observer_settings|select p.slug,s.projects_enabled,s.local_sessions_enabled,s.daily_batches,s.access_team_id is not null as team_restricted from public.observer_phase_settings s join public.phases p on p.id=s.phase_id" \
    "accounts|select (select count(*) from auth.users) as users,(select count(*) from public.teams) as teams" \
    "installations|select organization,enabled from private.observer_installations order by organization" \
    "beta_entry_function|select to_regprocedure('public.my_observer_phase()') is not null as deployed"; do
    echo "sql ${label_query%%|*}: $(sql "${label_query#*|}" 2>&1 | head -c 1500)"
  done
fi

if [ -n "${KIMI_API_KEY:-}" ]; then
  for url in https://api.moonshot.cn/v1 https://api.moonshot.ai/v1 https://api.kimi.com/coding/v1; do
    echo "kimi $url/models: $(code "$url/models" -H "Authorization: Bearer $KIMI_API_KEY")"
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
