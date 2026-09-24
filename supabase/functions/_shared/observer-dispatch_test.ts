import { assertEquals } from "@std/assert";
import { encryptCredential } from "./observer-model.ts";
import { dispatchPending } from "./observer-dispatch.ts";
import { GitHubError } from "./observer-github.ts";

Deno.test("dispatcher decrypts only the nonce and acknowledges the fixed workflow", async () => {
  const id = "00000000-0000-4000-8000-000000000001", key = btoa("k".repeat(32)), nonce = "n".repeat(43);
  const encrypted = await encryptCredential(nonce, id + ":nonce", key);
  const calls: string[] = [];
  const result = await dispatchPending((name) => {
    calls.push(name);
    return Promise.resolve(
      name === "observer_pending_jobs"
        ? [{
          id,
          kind: "engine",
          organization: "AGENTIC-OBSERVER26-runner-1",
          workflow_sha: "a".repeat(40),
          encrypted_nonce: encrypted,
        }]
        : null,
    );
  }, {
    dispatch: (org, workflow, job, token, sha) => {
      assertEquals([org, workflow, job, token, sha], [
        "AGENTIC-OBSERVER26-runner-1",
        "observer-engine.yml",
        id,
        nonce,
        "a".repeat(40),
      ]);
      calls.push("github");
      return Promise.resolve();
    },
  }, key);
  assertEquals(result, [{ id, dispatched: true }]);
  assertEquals(calls, [
    "observer_reconcile_jobs",
    "observer_reconcile_sessions",
    "observer_pending_jobs",
    "github",
    "observer_mark_dispatched",
  ]);
});

Deno.test("ambiguous dispatch errors retain a recoverable receipt without exposing credentials", async () => {
  const id = "00000000-0000-4000-8000-000000000001", key = btoa("k".repeat(32));
  const encrypted = await encryptCredential("n".repeat(43), id + ":nonce", key);
  const calls: { name: string; args: Record<string, unknown> }[] = [];
  const result = await dispatchPending(
    (name, args) => {
      calls.push({ name, args });
      return Promise.resolve(
        name === "observer_pending_jobs"
          ? [{
            id,
            kind: "execute",
            organization: "AGENTIC-OBSERVER26-runner-1",
            workflow_sha: "a".repeat(40),
            encrypted_nonce: encrypted,
          }]
          : null,
      );
    },
    { dispatch: () => Promise.reject(new GitHubError("github_unavailable")) },
    key,
  );
  assertEquals(result, [{ id, dispatched: false, error: "github_unavailable" }]);
  assertEquals(calls.at(-1), { name: "observer_dispatch_error", args: { p_job: id, p_error: "github_unavailable" } });
});
