# Participant model API keys for formal runs

Formal runs never use organizer model credits. "Formal" means every run for which
`private.observer_personal_models_only()` is true: runs in a phase that counts for
the final ranking or has the slug `online`, and every run (including model-assisted
project preparation) while the site is in competition mode. Other runs, such as
the practice/acceptance paths outside competition mode, keep their existing
behaviour. Deterministic projects need no API.

Each team chooses in the workspace section **Model API (optional)**:

| | Save encrypted (default, recommended) | Do not save (page relay) |
|---|---|---|
| Key location | AES-GCM ciphertext in `private.observer_providers` | only the open page's memory |
| Page must stay open | no | yes, until each evaluation finishes; also at the time agreed for top-team verification |
| Call path | model proxy calls the provider directly | model proxy → Broadcast → open page → portal → provider |
| Per-run bounds | phase settings: 10,000 calls, 10,000,000 tokens; one call at a time | 10,000 calls; one outstanding call |
| Size caps | 64 KiB request, 192 KiB response | 64 KiB request, 192 KiB response |

A team that has not chosen is in stored mode. Choosing "Do not save" deletes a
saved key immediately (`observer_set_team_model_mode('relay')`, same transaction).
Saving a key selects stored mode again. Only team members (not banned) can change
the choice or manage the key; it is team-wide.

## Stored mode

1. A member selects an approved HTTPS endpoint, enters the model and key, and
   saves (`save_team_model` portal action, over HTTPS). The portal accepts only an
   exact HTTPS entry of `OBSERVER_MODEL_BASES` (the HTTP test exception never
   applies), creates a new provider ID and encrypts the key with the Edge
   application key `OBSERVER_KEY_ENCRYPTION_KEY` (AES-GCM, provider ID as
   additional data). Only the ciphertext and, for keys of at least 16 characters,
   the last four characters as a recognition hint reach the database
   (`observer_save_team_model`, service role only). One key per team; saving
   again replaces it and wipes the previous ciphertext.
2. Clients only ever receive `{mode, saved: {base_url, model, key_hint, saved_at}}`.
   No API returns the key or ciphertext.
3. The project keeps using the scoped `OPENAI_BASE_URL`/`OPENAI_API_KEY` of its
   run. `observer_model_route` answers `{personal: true, mode: "stored"}` and the
   proxy reserves the call with `observer_reserve_team_model`. It checks the run
   capability and deadline, the per-run call/token limits and one outstanding
   call, and returns only the run team's own saved provider. Without a saved key
   the call fails with `team_model_not_configured` (HTTP 403). No organizer,
   shared, legacy or other-team provider is ever substituted; the
   `a_disallow_stored_formal_model` trigger on `private.observer_model_calls`
   enforces this again for every call receipt.
4. The Edge function re-checks the base against the current allowlist (HTTPS, no
   credentials, query or fragment), decrypts the key in request memory only,
   sends one non-streaming request with `redirect: "error"` using the saved model
   name (the project's `model` value is replaced), redacts the key from the
   response and drops its reference. Usage reported by the provider is settled;
   unknown usage is charged at the reserved upper bound.
5. Provider bodies, headers, redirects and exception text are never forwarded;
   the project receives only an error code.

The key never enters project containers, job payloads or Actions inputs (projects
receive only their scoped run credential), run artifacts, logs, audit-log details
(team, user and base URL only) or error messages.

`observer_delete_team_model` (and choosing relay mode) wipes the key at once. A
provider row referenced by call receipts keeps only non-secret metadata (base URL,
model name) with an empty `encrypted_key`; unreferenced rows are deleted. Calls
already in flight may finish. A team that saved a key but never made a call must
delete the key before it can be disbanded (the row references the team).

## Relay mode ("Do not save")

Unchanged ephemeral flow. The participant selects a supported HTTPS base, model
and key in the workspace; they stay in Vue memory without browser storage. Each
active run gets an unguessable Broadcast channel, readable only by the owning
team. The proxy reserves a call ID and broadcasts the prompt; the open page
submits it with the key to the authenticated portal, which verifies team
ownership and the exact prompt digest, claims the call once and calls only an
approved HTTPS provider with redirects disabled. The database stores the channel
and call receipts, never the key, ciphertext, prompt or response. Without an
attached page the call fails within the bounded wait; there is no organizer
fallback. The relay functions refuse teams in stored mode
(`personal_model_not_enabled`; `observer_personal_model_routes` returns no
routes). Do not use SQL `realtime.send()` for this relay: database Broadcast
persists messages (https://supabase.com/docs/guides/realtime/broadcast).

If a relay-mode team is verified as a top team after the competition, its page
must be open at the time agreed with the organizers so the re-run can call its
model.

## Organizer steps

Deploy in this order: `scripts/deploy-observer-backend.py --apply` (migration
`20260926000200_stored_model_keys`; the script now applies every migration from
`20260925000100` onward and records each hash), then the Edge functions
`observer-model` and `observer-portal`, then the website. Formal model calls fail
closed in between.

The allowlist is the `OBSERVER_MODEL_BASES` function secret (exact bases,
comma-separated) written by `scripts/configure-observer-secrets.py`: the
organizer HTTP test base (also in `OBSERVER_MODEL_HTTP_BASES`, never usable for
saved keys), `https://openrouter.ai/api/v1`, `https://api.deepseek.com` and any
`--model-base` additions made when it was run. Kimi Coding
(`https://api.kimi.com/coding/v1`) and the GLM endpoints are not in the script's
defaults; add them there if they should be offered.

Formal phases get explicit per-run model limits in `public.observer_phase_settings`
(`model_call_limit` 10,000, `model_token_limit` 10,000,000, `model_concurrency` 1).
The migration sets them for existing formal phases and
`configure-observer-competition.py` uses them for new ones. Runs opened earlier
keep the limits they started with.

### Purge after the results are verified

Run with the service role, for example in the SQL editor or management SQL API:

```sql
select public.observer_purge_provider_keys();  -- returns the number of keys deleted
select count(*) from private.observer_providers
  where team_id is not null and encrypted_key <> '';  -- expect 0
```

or `POST /rest/v1/rpc/observer_purge_provider_keys` with the service-role key.
It wipes every participant-owned key (saved team keys and keys retained from the
former provider settings), removes the saved-key records and writes an
`observer.provider_keys_purged` audit entry with the count. Organizer providers
(`team_id is null`) are untouched and call receipts remain. It is idempotent and
returns 0 when nothing is left; keys saved afterwards are not covered, so re-run
it if teams save again.

## Validation

- `tests/test_personal_models.py` (real PostgreSQL): save, replace, delete,
  team isolation, no key or ciphertext in any participant-visible result,
  stored-mode reservations use only the team's own key, no organizer fallback in
  either mode, choosing relay deletes the key, relay claims and receipts, one
  outstanding call and per-run limits, purge, and the migration's limit update.
- `observer-model_test.ts`, `observer-portal_test.ts`: HTTPS/approved-host and
  redirect rules, decryption per request, redaction, response cap, no fallback,
  encryption before storage. `observer-personal-model_test.ts`: relay behaviour.
- `tests/test_project_http.py`: real Deno Edge functions, PostgREST and an HTTPS
  stub provider trusted through a throwaway test CA: a formal run calls the saved
  provider with the saved key and model, redirects and provider errors are not
  forwarded, deleting the key stops use, relay mode fails closed without any
  server-side call, and the plaintext key appears in no table or Edge log.
- `tests/test_project_portal_browser.py`: default stored mode, save with masked
  hint, switch to relay (key deleted), relay key not kept in browser storage,
  switch back, headings in all four languages.
- Opt-in: `integration/deployed-personal-model.ts` (selects relay mode first,
  which deletes that team's saved key) and `integration/personal-broadcast_test.ts`.

A live check with a real provider through the deployed proxy is still required
before relying on either mode; these tests use stubs and synthetic keys.
