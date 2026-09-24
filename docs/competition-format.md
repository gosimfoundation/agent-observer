# Competition format: what the platform implements

The participant UI presents one current competition, selected by the administrator.
The single `/compete` workspace replaces the former submission and project pages;
old links redirect there. Its workflow follows the configured phase, project
versions and evaluation batches. A prominent Submit button links to that workspace.

## Current policy (2026-09-24)

| | Current Playground | Formal competition after the administrator switches |
|---|---|---|
| Entry | `/compete` | `/compete` |
| Input | locally generated `decisions.csv` | complete repository or private project ZIP; no CSV |
| Execution | participant computer, original scorer | approved project version, platform-controlled sequential observations |
| Scenario | existing public scenarios | a new secret random seed per team and attempt, calibrated difficulty |
| Ranking | best score per scenario, unchanged | best complete batch, mean calibrated score over all scenarios |
| Model | optional | optional; participant supplies API and quota, no organizer credits |
| Personal credentials | never include in results | HTTPS only, browser/request memory only, never persisted |

Formal evaluation accepts a decision only for its current sequence, records it,
then publishes the next observation. Private seeds, frozen generator/calibration
versions and immutable decisions support independent reconstruction and scoring.
CSV remains an exported result artifact, not a formal submission format.

See `randomized-evaluation.md` for calibration and
`ephemeral-personal-models.md` for the personal API flow. Existing scores and
submissions are not deleted or rewritten by the migration.

## The coverage term

A score that only adds up per-tile science is indifferent to where the tiles come from: once scarcity forces an
agent to skip work, it can abandon whole regions for free. `challenge-score-v3` therefore gained one additive term:

```
coverage_bonus = coverage_bonus_weight × base_science_score × coverage_evenness
```

`coverage_evenness` is Jain's fairness index over the per-region counts of completed tiles — 1.0 when finished
tiles spread evenly across the eight regions, 1/8 when one region took everything, 0 when nothing was observed.
The weight lives in each scenario's `score_config.json` and defaults to 0, so scenarios that never set it are
unaffected by the term. Only `eval-a` and `eval-b` set it, at 0.35 — there the term is worth roughly a fifth of
a competitive run's total, and measured strategy differences reach ~2% of total, twenty times the ±0.1% spread
the challenge produced without it.

## The anomaly release (protocol v2 / snapshot v3 / weather v2)

The mechanics are **per scenario**, gated by the anomaly sections of `score_config.json`: the
online-competition scenarios (and the kit's `finals-preview`) enable them, while every practice scenario
keeps the pre-anomaly contract byte for byte — same snapshots, same scores, and previously uploaded v1
agent packages keep running there unchanged. On the enabled scenarios the contract adds the
anomaly-detection game on top of the survey:

- **Efficiency jitter + instrument faults.** Baseline `instrument_efficiency` is drawn per slot in [0.90, 1.00]
  and frozen at generation. One `instrument_fault` event per scenario (region-scoped, efficiency multiplier down
  to 0.10) starts mid-survey and has no natural lifetime (`persists_until_survey_end`): it ends only when a
  correct agent report completes the repair clock. Faults are never forecast and never appear in agent
  snapshots; they only act on the scorer's effective weather.
- **Hidden tile tags.** `outputs/reference/tile_anomalies.csv` (generated from `tile_config.json`
  `anomaly_tags` counts) marks tiles `nova` (score ×1.5) or `reddening` (×0.8, stacking). The multipliers are
  published in `score_config.json`; the tagged tiles are hidden from snapshots only — the truth file ships with
  practice scenarios and stays auditable.
- **Realized-score feedback.** Every snapshot carries `tile_last_finished: {tile_id, score} | null` — the
  realized official score of the most recently finished exposure (interrupted exposures report 0). Snapshot
  weather never carries `instrument_efficiency` and the preview baseline is efficiency-free, so comparing the
  two isolates the hidden instrument side (jitter × fault multiplier × tag multiplier).
- **Report channel.** `decision_response` accepts an optional `reports` array (`Instrument_Failure`, or
  `NOVA` / `Reddening` with a `tile_id`). Reports cost no slot time. Malformed entries are dropped without
  killing the action; duplicates are tolerated. Tags settle at final scoring: first report per (tile, tag),
  +100 correct / −150 wrong (`reporting` section of `score_config.json`). Fault reports drive an in-run
  lifecycle: a correct report (an unacknowledged fault active) publishes `fault_status` after
  `fault_response.response_latency_days` (1 d) at night starts and completes the repair after
  `repair_duration_days` (2 d), which truncates the fault's multiplier; a report with no active fault is a
  misreport — one free per correct report (`fault_misreport_free_allowance`), then `fault_misreport_penalty`
  (100) each, counter resetting on every correct report; re-reporting an acknowledged fault under repair is
  neutral. Misreports get a one-night `"status":"normal"` answer on the same latency schedule.
- **Repeat observations.** `duplicate_tile` is gone: re-observation is legal and a tile's science score is the
  maximum over its observations; completion, REQUIRED-miss relief and flexible quotas still bank on the first
  legal observation; request visits decouple from tile scores (a request on a previously observed tile needs a
  new post-issue observation to count a visit). `avoidable_wait` counts a wait as avoidable when an unfinished
  tile could complete or a repeat could beat the tile's banked best.
- **Audit chain.** Accepted reports are flattened into `decisions.csv` as `report_instrument_failure` /
  `report_nova` / `report_reddening` action rows (sharing the incrementing `decision_id` sequence), so the
  single trace file replays everything and its SHA-256 covers reports too. The baseline anchor is
  `23430.568406` (test constant, starter-kit README, SKILL.md).

Calibration knobs: `score_config.json` sections `repeat_observation` / `reporting` / `anomaly_tags` /
`fault_response`; `weather_config.json` `quality.instrument_efficiency.jitter_minimum/maximum` and
`events.instrument_fault` (including its `instrument_efficiency_multiplier_range`); `tile_config.json` `anomaly_tags`; the reference agent's detection thresholds are
the `SAC_ANOMALY_*` environment variables documented in `agent/anomaly_detection.py`.

## Where each piece lives

| Concern | Code |
|---|---|
| Submission kind (`results` \| `agent`) | `public.submission_kind` enum, `supabase/migrations/20260909000100_core.sql` |
| Which kinds a phase accepts | `phases.allow_results` / `phases.allow_agents`, enforced in the `create_submission` RPC |
| Which scenarios a phase uses | `phase_scenarios`, seeded in `worker/main.py` (`DEFAULT_SCENARIOS`, `seed()`) |
| Per-file visibility of a scenario | `scenarios.weather_public` / `forecasts_public` / `events_public`; enforced when the scenario is published to storage |
| Results-file evaluation | `worker/main.py` `evaluate()`, `kind == "results"` branch: the upload becomes `decisions.csv` and goes straight to the scorer |
| Hosted agent run | `worker/challenge_runner.py` via `evaluate()`, `kind == "agent"`: per-run venv, scrubbed environment, rlimits, one global wall clock, process-group kill at the cutoff |
| Agent transport | `challenge/run_challenge.py` (`JsonLineAgentProcess`), protocol `participant-agent-protocol-v2` |
| Scoring | `challenge/scoring_core.py`, the science team's scorer plus one additive coverage-uniformity term (off by default); weights in `scoring/score_config.json` |
| Replay visualization | `challenge/replay.py` + `challenge/templates/decision_replay.html`; produced for both kinds and uploaded as `decision_replay.html` |
| Local equivalent of the hosted run | `starter_kit/local_runner.py` — same transport, same environment rules, same scorer |

## Scenario generation

All scenarios come from one generator, `challenge/scenario_builder.py`, driven by the tile, weather, calendar and
request simulators delivered by the science team. A scenario is a directory of `config/*.json` plus
`outputs/reference/*.csv`, checksummed and validated by the authoritative scorer before it is registered.

```bash
# public practice scenario, everything downloadable
python -m worker.main gen-scenario --slug demo-week --seed 20261005 --days 7 --start-date 2026-10-05 --wallclock 900

# competition scenario, weather and forecasts withheld
python -m worker.main gen-scenario --slug eval-c --seed 777 --days 30 --start-date 2026-10-05 --wallclock 3600 \
  --hidden-weather --hidden-forecasts --regions 8 --tiles-per-region 200 --coverage-weight 0.35
```

The `demo-week` parameters above are the same ones that produced `starter_kit/scenarios/demo-week`, so the copy in
the downloaded kit and the copy the platform publishes are the same scenario.

## Open operational items

These are decisions for the organizers, not code changes:

- Rotate the seeds of `eval-a` / `eval-b` before the online phase. The seeds and the generator are public, so any
  scenario whose parameters have been published can be rebuilt locally — hidden weather is only hidden while the
  parameters are. A rotation reads catalogue size and coverage weight off the published scenario, so it changes
  the weather and nothing else; the reference defaults (64 tiles, no coverage term) only apply when a scenario's
  config cannot be read back. Rotation also redraws the hidden `tile_anomalies.csv` tags and the
  `instrument_fault` events, since both derive from the scenario seed.
- Practice-phase `results` uploads are a bare `decisions.csv` — which now also carries any `report_*` rows, so
  practice scoring settles reports exactly like hosted runs.
- Decide how many worker runners to keep alive during the online phase. A 1–2 h wall clock per scenario means one
  runner serialises submissions.
