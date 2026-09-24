import { boundedJson, capability, ProxyError } from "./observer-model.ts";
import type { Rpc } from "./observer-model.ts";

export async function sessionRequest(request: Request, rpc: Rpc): Promise<unknown> {
  const { run, token } = capability(request.headers.get("authorization"));
  const body = await boundedJson(request, 17 * 1024 * 1024);
  if (!body || typeof body !== "object" || Array.isArray(body) || typeof body.action !== "string") {
    throw new ProxyError(400, "invalid_session_request");
  }
  const base = { p_run: run, p_token: token };
  // Fixed mapping: a request can never pick an arbitrary privileged RPC.
  switch (body.action) {
    case "abort":
      return await rpc("observer_abort_local", base);
    case "decisions":
      return await rpc("observer_export_decisions", base);
    case "status":
      return await rpc("observer_run_status", base);
    case "poll":
      if (body.scope !== undefined && body.scope !== "engine" && body.scope !== "participant") {
        throw new ProxyError(400, "invalid_scope");
      }
      return await rpc("observer_poll", {
        ...base,
        p_scope: body.scope ?? "participant",
        p_initialized: body.initialized === true,
      });
    case "ready":
      return await rpc("observer_ready", base);
    case "respond":
      return await rpc("observer_respond", { ...base, p_sequence: body.sequence, p_response: body.response });
    case "initialize":
      return await rpc("observer_publish_initial", { ...base, p_publication: body.publication });
    case "begin":
      return await rpc("observer_begin", base);
    case "publish":
      return await rpc("observer_publish_step", {
        ...base,
        p_sequence: body.sequence,
        p_observation: body.observation,
      });
    case "commit":
      return await rpc("observer_commit_step", { ...base, p_sequence: body.sequence, p_committed: body.committed });
    case "finish":
      return await rpc("observer_finish_run", {
        ...base,
        p_summary: body.summary,
        p_decisions_digest: body.decisions_digest,
        p_result_path: body.result_path,
      });
    case "fail":
      return await rpc("observer_fail_run", { ...base, p_error: body.error });
    default:
      throw new ProxyError(400, "unknown_session_action");
  }
}
