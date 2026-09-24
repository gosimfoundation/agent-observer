# Personal APIs without saved credentials

Formal runs and all model-using preparation during competition mode use participant-owned APIs. The platform does not provide model
credits. Deterministic projects need no API. Existing stored-provider rows are
retained for audit but cannot fund formal runs; the old personal-key save API
returns `ephemeral_credentials_required` and cannot write another key.

## Flow

1. The participant selects a supported HTTPS base, model and key in the
   competition workspace. These values are Vue memory only, without browser
   storage. Connecting registers no API key on the server.
2. Each active run has a random Broadcast channel. Only the owning team can
   obtain its address. The database stores the channel and call receipt metadata,
   never the API key, ciphertext, prompt or response.
3. The agent uses its existing expiring OpenAI-compatible proxy credential. The
   proxy authenticates the run, reserves a call ID and broadcasts its prompt.
4. The open participant page receives the prompt and submits it with the personal
   credential via HTTPS to the authenticated portal. The portal verifies team
   ownership and the exact prompt digest, and claims the call once before billing.
5. The portal calls only an approved HTTPS provider with redirects disabled. It
   holds the key in request memory, redacts it from provider output and clears its
   reference. The sanitized result returns via transient client/REST Broadcast.
6. Closing the page clears the key and connections. Model requests without an
   attached page fail within the bounded wait; they never fall back to organizer
   credits. Reopening requires entering the key again.

Keep the workspace open during model-using runs, including model-assisted project
preparation. Using an already supplied interface does not require adaptation.

## Boundaries

- The model call is non-streaming, limited to a 64 KiB request and 192 KiB response.
- One outstanding personal call per run and at most 10,000 calls per run bound
  resource use. Upstream API quotas and costs belong to the participant.
- Claiming a call is atomic: duplicate browser tabs, retries and repeated
  Broadcast delivery cannot cause a second upstream request.
- Provider errors are not forwarded. Redirects and unapproved/non-HTTPS bases are
  rejected before sending a credential. Permanent keys never enter project
  containers, repository archives, Actions inputs, database functions or logs.
- Do not use SQL `realtime.send()` for this relay. Database Broadcast persists
  messages. The implementation uses client/REST Broadcast instead:
  https://supabase.com/docs/guides/realtime/broadcast
- Platform traces may contain request IDs and status, not API-key request bodies.
  Synthetic fixtures are used when recording browser/network acceptance traces.

## Validation

`tests/test_personal_models.py` checks ownership, call ordering, concurrent claims,
old-provider rejection and persisted field boundaries in real PostgreSQL.
`observer-personal-model_test.ts` checks HTTPS destination restrictions, duplicate
claims, provider failures, response redaction and no organizer fallback.
The portal browser journey checks that connecting does not save the key and a
reload empties the field. The opt-in integration/personal-broadcast_test.ts also exercises the real hosted
Broadcast transport for success and failure, using synthetic credentials and a
stub provider without account creation or billing. Live HTTPS-provider acceptance
is still required before declaring the entire deployment complete.

`integration/deployed-personal-model.ts` additionally exercises the deployed
proxy, team-authenticated portal and real Broadcast against a disposable active
run. A synthetic invalid provider credential must produce a redacted failure
without organizer fallback. Its privileged test configuration is supplied only
over stdin; it does not write configuration, change decisions or incur model
charges. A passing negative check is not evidence of a successful real model call.
