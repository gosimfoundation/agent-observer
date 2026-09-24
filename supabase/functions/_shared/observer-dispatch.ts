import { decryptCredential } from "./observer-model.ts";
import type { Rpc } from "./observer-model.ts";
import { GitHubApp, GitHubError } from "./observer-github.ts";

export async function dispatchPending(rpc: Rpc, app: Pick<GitHubApp, "dispatch">, masterKey: string) {
  await rpc("observer_reconcile_jobs", {});
  await rpc("observer_reconcile_sessions", {});
  const jobs = await rpc("observer_pending_jobs", { p_limit: 10 });
  const outcomes = [];
  for (const job of jobs) {
    try {
      const nonce = await decryptCredential(job.encrypted_nonce, job.id + ":nonce", masterKey);
      await app.dispatch(
        job.organization,
        "observer-" + job.kind + ".yml" as Parameters<GitHubApp["dispatch"]>[1],
        job.id,
        nonce,
        job.workflow_sha,
      );
      await rpc("observer_mark_dispatched", { p_job: job.id });
      outcomes.push({ id: job.id, dispatched: true });
    } catch (error) {
      const code = error instanceof GitHubError ? error.code : "dispatch_unavailable";
      await rpc("observer_dispatch_error", { p_job: job.id, p_error: code });
      outcomes.push({ id: job.id, dispatched: false, error: code });
    }
  }
  return outcomes;
}
