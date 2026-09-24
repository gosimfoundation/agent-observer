import { createClient } from "npm:@supabase/supabase-js@2";
import { chatCompletion, decryptCredential, ProxyError } from "../_shared/observer-model.ts";

const cors = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "POST, OPTIONS",
  "access-control-allow-headers": "authorization, content-type, apikey, idempotency-key",
  "access-control-expose-headers": "x-observer-request-id",
};
const service = createClient(Deno.env.get("SUPABASE_URL") ?? "", Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "", {
  auth: { persistSession: false },
});
const bases = (key: string) =>
  new Set((Deno.env.get(key) ?? "").split(",").map((s) => s.trim().replace(/\/$/, "")).filter(Boolean));
const knownErrors: Record<string, [number, string]> = {
  invalid_or_expired_capability: [401, "invalid_or_expired_capability"],
  session_deadline: [401, "session_deadline"],
  run_model_quota: [429, "run_model_quota"],
  provider_model_quota: [429, "provider_model_quota"],
  model_not_available: [403, "model_not_available"],
  request_id_conflict: [409, "request_id_conflict"],
};

Deno.serve({ port: Number(Deno.env.get("OBSERVER_LISTEN_PORT") ?? 8000) }, async (request) => {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  try {
    if (request.method !== "POST" || !new URL(request.url).pathname.endsWith("/v1/chat/completions")) {
      throw new ProxyError(404, "endpoint_not_found");
    }
    const response = await chatCompletion(request, {
      rpc: async (name, args) => {
        const { data, error } = await service.rpc(name, args);
        if (error) {
          const known = knownErrors[error.message];
          throw new ProxyError(known?.[0] ?? 503, known?.[1] ?? "model_accounting_unavailable");
        }
        return data;
      },
      fetch,
      decrypt: (value, provider) =>
        decryptCredential(value, provider, Deno.env.get("OBSERVER_KEY_ENCRYPTION_KEY") ?? ""),
      allowedBases: bases("OBSERVER_MODEL_BASES"),
      allowedHttpBases: bases("OBSERVER_MODEL_HTTP_BASES"),
      defaultProvider: Deno.env.get("OBSERVER_DEFAULT_MODEL_PROVIDER") ?? "",
    });
    for (const [name, value] of Object.entries(cors)) response.headers.set(name, value);
    return response;
  } catch (error) {
    const status = error instanceof ProxyError ? error.status : 503;
    const code = error instanceof ProxyError ? error.code : "model_proxy_unavailable";
    // Never forward database/provider exception messages, headers or credentials.
    return new Response(JSON.stringify({ error: { type: "observer_error", code, message: code } }), {
      status,
      headers: { ...cors, "content-type": "application/json" },
    });
  }
});
