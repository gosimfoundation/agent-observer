import { assert, assertEquals, assertRejects } from "@std/assert";
import type { SupabaseClient } from "npm:@supabase/supabase-js@2";
import { decryptCredential, ProxyError } from "./observer-model.ts";
import { keyHint, portalRequest } from "./observer-portal.ts";

const master = btoa("m".repeat(32));
const user = "20000000-0000-4000-8000-000000000001";
const key = "sk-team-fixture-abcdefghijklmnop-9Zq4";
type Call = { client: string; name: string; args: Record<string, unknown> };

function clients(status: unknown = { base_url: "https://api.example.test/v1", model: "glm-4.6", key_hint: "9Zq4" }) {
  const calls: Call[] = [];
  const client = (label: string) =>
    ({
      rpc: (name: string, args: Record<string, unknown> = {}) => {
        calls.push({ client: label, name, args });
        const data = name === "observer_delete_team_model"
          ? true
          : name === "observer_set_team_model_mode"
          ? args.p_mode
          : status;
        return Promise.resolve({ data, error: null });
      },
      storage: { from: () => ({}) },
    }) as unknown as SupabaseClient;
  return { calls, user: client("user"), service: client("service") };
}
function portal(body: Record<string, unknown>, c = clients()) {
  return portalRequest(new Request("https://portal.test", { method: "POST", body: JSON.stringify(body) }), {
    user: c.user,
    service: c.service,
    userId: user,
    masterKey: master,
    modelBases: ["https://api.example.test/v1", "http://organizer-test.example.test/v1"],
    httpBases: ["http://organizer-test.example.test/v1"],
  });
}

Deno.test("a saved key is encrypted before storage and never returned or sent to the database in plaintext", async () => {
  const c = clients();
  const result = await portal({
    action: "save_team_model",
    base_url: "https://api.example.test/v1/",
    model: " glm-4.6 ",
    key: "  " + key + "\n",
  }, c);
  assertEquals(c.calls.map((x) => [x.client, x.name]), [
    ["service", "observer_save_team_model"],
    ["user", "observer_team_model"],
  ]);
  const saved = c.calls[0].args;
  assertEquals(saved.p_user, user);
  assertEquals(saved.p_base, "https://api.example.test/v1");
  assertEquals(saved.p_model, "glm-4.6");
  assertEquals(saved.p_key_hint, "9Zq4");
  // Bound to the provider ID it was stored under; another ID cannot decrypt it.
  assertEquals(await decryptCredential(String(saved.p_encrypted_key), String(saved.p_provider), master), key);
  await assertRejects(() => decryptCredential(String(saved.p_encrypted_key), user, master), ProxyError);
  assert(!JSON.stringify(c.calls).includes(key));
  assert(!JSON.stringify(result).includes(key));
  assert(!JSON.stringify(result).includes(String(saved.p_encrypted_key)));
});

Deno.test("HTTP, unapproved and malformed model settings are refused before encryption or storage", async () => {
  const cases: [Record<string, unknown>, string][] = [
    [{ base_url: "http://organizer-test.example.test/v1", model: "m", key }, "model_destination_not_enabled"],
    [{ base_url: "https://unapproved.example.test/v1", model: "m", key }, "model_destination_not_enabled"],
    [{ base_url: "https://user:pw@api.example.test/v1", model: "m", key }, "model_destination_not_enabled"],
    [{ base_url: "https://api.example.test/v1", model: "", key }, "invalid_team_model"],
    [{ base_url: "https://api.example.test/v1", model: "m\nx", key }, "invalid_team_model"],
    [{ base_url: "https://api.example.test/v1", model: "m", key: "short" }, "invalid_team_model"],
    [{ base_url: "https://api.example.test/v1", model: "m", key: "has space inside-key" }, "invalid_team_model"],
    [{ base_url: "https://api.example.test/v1", model: "m", key: "x".repeat(8193) }, "invalid_team_model"],
  ];
  for (const [fields, code] of cases) {
    const c = clients();
    const error = await assertRejects(() => portal({ action: "save_team_model", ...fields }, c), ProxyError);
    assertEquals(error.code, code);
    assertEquals(c.calls.length, 0);
    assert(!error.message.includes(key));
  }
});

Deno.test("key hints reveal at most four characters and nothing for short keys", () => {
  assertEquals(keyHint("0123456789abcdef"), "cdef");
  assertEquals(keyHint("short-key-12345"), "");
});

Deno.test("deleting and choosing the mode use the caller's own team RPCs", async () => {
  const c = clients();
  assertEquals(await portal({ action: "delete_team_model", team_id: "someone-else" }, c), { deleted: true });
  assertEquals(await portal({ action: "set_team_model_mode", mode: "relay", team_id: "someone-else" }, c), {
    mode: "relay",
  });
  assertEquals(c.calls, [
    { client: "user", name: "observer_delete_team_model", args: {} },
    { client: "user", name: "observer_set_team_model_mode", args: { p_mode: "relay" } },
  ]);
  for (const mode of ["", "organizer", null]) {
    const rejected = clients();
    const error = await assertRejects(() => portal({ action: "set_team_model_mode", mode }, rejected), ProxyError);
    assertEquals(error.code, "invalid_team_model_mode");
    assertEquals(rejected.calls.length, 0);
  }
});

Deno.test("a repeat evaluation is only requested with an explicit confirmation", async () => {
  const phase = "30000000-0000-4000-8000-000000000001", revision = "30000000-0000-4000-8000-000000000002";
  const c = clients("batch");
  await portal({ action: "evaluate", phase_id: phase, revision_id: revision, confirm_repeat: "yes" }, c);
  await portal({ action: "evaluate", phase_id: phase, revision_id: revision, confirm_repeat: true }, c);
  assertEquals(c.calls.map((x) => x.args), [
    { p_phase: phase, p_revision: revision },
    { p_phase: phase, p_revision: revision, p_confirm_repeat: true },
  ]);
});

Deno.test("withdrawal uses the caller's team RPC and database refusals keep their codes", async () => {
  const revision = "30000000-0000-4000-8000-000000000002";
  const c = clients();
  assertEquals(await portal({ action: "withdraw", revision_id: revision }, c), { accepted: true });
  assertEquals(c.calls, [{ client: "user", name: "observer_withdraw_revision", args: { p_revision: revision } }]);
  await assertRejects(() => portal({ action: "withdraw", revision_id: "not-a-uuid" }, clients()), ProxyError);
  for (const code of ["revision_not_withdrawable", "revision_already_evaluated", "revision_withdrawn", "other"]) {
    const refused = {
      user: { rpc: () => Promise.resolve({ data: null, error: { message: code } }) } as unknown as SupabaseClient,
      service: clients().service,
    };
    const error = await assertRejects(
      () => portal({ action: "withdraw", revision_id: revision }, { ...refused, calls: [] }),
      ProxyError,
    );
    assertEquals(error.code, code === "other" ? "portal_request_failed" : code);
  }
});
