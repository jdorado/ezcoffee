# EzCoffee migration checklist

## Goal

Move EzCoffee's agentic features to the native Ez engine without rebuilding the
coffee journal. Keep the existing minimalist frontend, FastAPI application, and
MongoDB records; make Ez the only owner of agent conversations, native sessions,
context, reasoning, model/provider selection, tool choice, and continuation.

The coffee application remains the owner of authentication, account scope,
canonical coffees and shots, deterministic validation, and the human UI. A
narrow installed EzCoffee plugin exposes only the bounded coffee operations Ez
needs and returns canonical receipts. Direct OpenRouter calls, direct TypeSafe
calls, and the private raw Codex sidecar are transitional paths, not the target
architecture.

This is a product checklist, not an implementation guide. Each group is
approved and QA'd before the next one begins.

> Migration remains active until every enabled AI profile reaches the native
> path 'EzCoffee UI → EzCoffee API → Ez → EzCoffee plugin/API → Ez → UI', and
> no direct model runner or provider path remains. The 'selfhost' profile stays
> intentionally AI-free.

## Current status — 2026-09-20

Migration is in **pre-migration → shared Ez boundary**.

- [x] The journal has a small canonical product model: coffees, shots, and a
  revisioned brew profile in MongoDB.
- [x] The self-hosted profile fails closed with no authentication, chat, or AI.
- [x] Hosted chat has verified account scoping and bounded record context, but
  it still calls OpenRouter directly from the FastAPI application.
- [x] The private profile has a scoped Codex sidecar and gateway receipts, but
  it still runs a product-specific agent runner outside Ez.
- [x] The frontend consumes canonical API state and does not call a model
  provider directly.
- [ ] Install and verify a narrow EzCoffee plugin through the standard Ez path.
- [ ] Route one real native Ez conversation through the coffee product and
  preserve its session across reload and follow-up turns.
- [ ] Remove direct OpenRouter/TypeSafe inference and the raw Codex sidecar from
  all supported AI profiles.

## Repository map

| Role | Path | Use it for |
| --- | --- | --- |
| **EzCoffee product — implementation target** | [ezcoffee/](.) | The frontend, API, tests, profiles, and migration documentation. |
| **Human UI** | [coffee_app/](coffee_app) | Render coffees, shots, plans, receipts, and chat projections; never own agent context or tool choice. |
| **Canonical domain/API** | [coffee_api/src/](coffee_api/src) | Authenticated account scope, Mongo persistence, revision checks, deterministic coffee rules, and API readback. |
| **Direct provider paths — migration sources** | [coffee_api/src/services/openrouter.py](coffee_api/src/services/openrouter.py), [coffee_api/src/services/typesafe.py](coffee_api/src/services/typesafe.py) | Evidence of current behavior; remove or reduce to deterministic code after the Ez path is accepted. |
| **Raw Codex sidecar — migration source** | [coffee_api/coffee_ai/](coffee_api/coffee_ai) | Preserve only long enough to compare behavior and protect continuity; it is not a new implementation target. |
| **Agent instructions and private data boundary** | [coffee_api/coffee_ai/workspace/AGENTS.md](coffee_api/coffee_ai/workspace/AGENTS.md), ignored 'data/' and runtime files | Move durable agent guidance into the native Ez workspace; keep personal records, credentials, and native sessions outside Git. |
| **Runtime profiles** | [compose*.yml](.), [profiles/](profiles), [ops/](ops) | Keep self-host, hosted, and personal boundaries explicit while replacing the private AI runtime with the standard Ez binding. |
| **Ez platform** | [../ez/](../ez) | Shared engine, authorization, transport, native sessions, plugin installation, and receipts. Shared defects belong there. |
| **AIFit migration reference** | [../aifit/migration.md](../aifit/migration.md) | Reuse the migration structure and ownership principles; do not copy AIFit's domain model or workflows. |

Only this repository is the EzCoffee product implementation target. The narrow
EzCoffee plugin lives product-side at `plugins/coffee/`, mirroring the AIFit
pattern (`aifit/plugins/aifit/`), and is installed through the standard Ez
plugin path. Changes to Ez core itself belong in the Ez repository. Every
step must be verified through the installed Ez path before this migration
can claim completion.
Direct provider paths and the raw sidecar below are migration sources to
replace or retire, not architecture to reproduce; do not build new features
on them.

> **Open-source standard:** `ezcoffee/` will be public. Treat every change as
> public code: keep secrets, real coffee data, private URLs, tokens, account
> registries, native sessions, and deployment state outside the repository;
> use only safe examples and documented configuration placeholders.

## Non-negotiables

- Preserve the useful coffee-journal experience and the dense minimalist UI;
  changing product scope requires a separate decision.
- Ez owns agent sessions, context, reasoning, provider/model selection, tool
  choice, continuation, and any agent channel delivery.
- EzCoffee owns verified account boundaries, coffees, shots, brew profiles,
  revision-safe domain writes, and the API/frontend projections of those
  records.
- The EzCoffee plugin is deterministic and narrow. It must not contain a model
  loop, prompt builder, transcript replay, scheduler, database authority, or
  product-specific agent runner.
- The plugin is the ONLY execution surface: the agent authors typed JSON and
  streams it over stdin; every write carries an idempotent `--request-id` and,
  for revisions, `--expected-revision`. Artifacts carry no credentials, owner
  or account identifiers, private URLs, or capabilities. Ez derives authority
  from the bound run and the API validates it again.
- No agent-facing operation may bypass an installed Ez plugin with a host
  process, direct provider call, raw Codex subprocess, or application-owned
  orchestration path.
- The native agent must never receive database credentials, arbitrary account or
  tenant identifiers, private URLs, or an unrestricted write token. Ez derives
  authority from the bound run and the API validates it again.
- Mongo coffees and shots remain canonical and revisioned. Planned tests remain
  separate from logged shots; recipe reuse never copies measured outputs or
  tasting results.
- Every mutation needs an idempotent request key where applicable, a canonical
  receipt, and readback before the UI or agent claims success.
- Public 'selfhost' remains anonymous and AI-free. Hosted and personal AI are
  opt-in profiles and must fail closed when Ez is unavailable or unbound.
- Move a user outcome only after it works end to end through a real native Ez
  turn; mocks, health checks, queued jobs, or a direct API smoke test are not
  migration proof.

## Migration order

### 1. Shared foundation and native chat

- [ ] Inventory every current chat, recommendation, retry, job, message, and
  sidecar path and mark it **preserve**, **replace**, **retire**, or **WIP**.
- [ ] Create one isolated development Ez binding for a real authenticated
  EzCoffee account; derive the binding from the verified account, never from
  browser-supplied owner data.
- [ ] Move the concise coffee-agent role and durable coffee rules into the
  native Ez workspace without rebuilding the conversation in the API.
  Seed it from a short tenant role (capability list plus receipt rule, as in
  the AIFit tenant `AGENTS.md` pattern); native Markdown stays the context,
  never an API-built transcript.
- [ ] Define the smallest EzCoffee plugin surface for scoped coffee reads when
  native context cannot provide a needed fact and revision-safe coffee/shot
  writes when the agent is authorized to mutate a record. Target three
  writes maximum: create or update a coffee, create or update a shot, and
  synchronize the existing planned next shot — each through the installed
  plugin CLI with `--request-id` and `--expected-revision`.
- [ ] Install the reviewed plugin with the bound Ez launcher and verify its
  help, permissions, input contract, and canonical receipt.
- [ ] Make one real chat work end to end: EzCoffee UI → EzCoffee API → Ez →
  EzCoffee plugin/API → EzCoffee UI.
- [ ] Keep the native Ez session as conversation authority across reload and
  follow-up messages. App messages or jobs records may remain a delivery
  projection, but they must not become a second prompt-history engine.
- [ ] Make repeated request admission and retry idempotent so one user request
  cannot create duplicate native work or duplicate coffee/shot writes.
- [ ] Verify that the agent can discuss a coffee without writing, and can log or
  edit a coffee/shot only when the request authorizes that action.
- [ ] Verify a second isolated account cannot see the first account's records,
  native context, session, or plugin capability.

QA: use one real signed-in account to ask for advice, log a new shot, update a
planned shot, reload, and continue the conversation. Read the native Ez turn,
the plugin receipt, and the canonical Mongo/API record; then repeat the read-only
conversation with a second account and confirm isolation. Record dated Live QA
entries here as in the AIFit reference (date, accounts, receipt, readback).

Live QA: pending — no native Ez turn verified yet.

### 2. Coffee domain capabilities

#### Canonical reads and context

- [ ] Keep the current-record context bounded to the selected coffee, relevant
  recent logged shots, the one planned next shot, and the necessary profile or
  equipment settings.
- [ ] Treat record text and imported logbook content as data, never as agent
  instructions.
- [ ] Prefer native Ez context plus a scoped application fact over an API-built
  transcript. Add a plugin read only when the native turn genuinely lacks the
  canonical fact needed for the request.
- [ ] Keep the original Markdown logbook as historical reference; current
  revisioned Mongo records win whenever they disagree.

#### Coffee and shot actions

- [ ] Support the minimum authorized actions: create or update a coffee, create
  or update a shot, and synchronize the existing planned next shot when a
  concrete recommendation changes it.
- [ ] Preserve account scope, exact record IDs, current revisions, archived
  coffee rules, timezone-aware recorded_at, and stale-write rejection.
- [ ] Preserve the distinction between a planned recipe and a brewed shot;
  never claim a plan was brewed and never copy yield, time, taste, rating, or
  other measured results into a reused recipe.
- [ ] Return the saved canonical record and receipt to the native Ez turn so the
  agent reports only verified outcomes.
- [ ] Decide the final disposition of deletion, import, archive, and restore
  actions explicitly; do not expose a broad generic CRUD command merely to
  simplify the migration.

#### Next-shot recommendation

- [ ] Remove the direct TypeSafe/JEV inference path from the API, or reduce the
  candidate builder to deterministic code and let native Ez choose and explain
  the next test.
- [ ] Keep the one-variable-at-a-time coffee rules and the existing planned-shot
  revision semantics in the canonical domain boundary.
- [ ] Ensure the frontend's fast next-shot card is a projection of the saved
  planned record, not a second AI conversation or unsaved model result.

QA: from native Ez, compare recent logged shots, request a next test, change one
recipe variable, and verify that the existing planned record is updated with a
receipt while all measured fields remain empty. Brew and log a separate shot,
then verify the planned and logged records remain distinct after reload and
retry.

### 3. Personal profile cutover

- [ ] Provision one private Ez owner/binding for the maintainer's verified
  account and keep its credentials, native session state, Mongo data, and URLs
  outside the repository.
- [ ] Migrate the current coffee-agent instructions and useful profile context
  into the native Ez workspace; do not reproduce the sidecar's prompt assembly
  or transcript as application state.
- [ ] Preserve useful conversation continuity through the supported native Ez
  session/import path where available. If a clean native session is required,
  retain the old sidecar state read-only and make the reset explicit before
  cutover.
- [ ] Run the personal web chat through Ez and verify a real coffee/shot write,
  canonical receipt, and API/UI readback.
- [ ] Replace the 'compose.personal.yml' AI sidecar path with the standard Ez
  binding/transport used by the deployment; no private launcher wrapper may
  select a model or own the conversation.
- [ ] Confirm personal owner authentication still rejects every other account
  and that the personal profile remains unavailable in the public self-host
  and hosted configurations.

QA: use the real personal account to continue a coffee conversation, ask for a
recommendation, log a shot, edit it with a current revision, reload, and retry
an uncertain request. Verify the native session, Ez/plugin receipt, API record,
and UI projection all refer to the same account and action.

### 4. Hosted onboarding and account isolation

- [ ] Replace the shared hosted OpenRouter path with one Ez binding/profile per
  verified account, or explicitly mark hosted AI WIP until that isolation is
  available; do not share a native session between hosted users.
- [ ] Keep provider credentials and model policy in the canonical Ez host
  binding, not in browser configuration, the public API, or an app-side router.
- [ ] Create or reuse one hosted Ez profile per account without duplicating
  accounts, bindings, or native sessions when onboarding is retried.
- [ ] Show whether Ez setup is ready, pending, or unavailable, and fail closed
  rather than silently falling back to direct OpenRouter or anonymous chat.
- [ ] Verify hosted read/write, profile settings, planned shots, and chat are
  all scoped by the verified Privy subject.
- [ ] Keep the free hosted product scope unchanged: no billing or provider
  choice is added as part of this migration.

QA: use two real hosted accounts. Each account signs in, continues its own
native conversation, reads its own coffee history, and logs a shot. Verify that
neither account can read or mutate the other's records, context, receipts, or
session, including after retry and reload.

### 5. Legacy review, removal, and cutover

- [ ] Record the final disposition of every direct agent path in this document:
  **preserve**, **replace**, **retire**, or **WIP**.
- [ ] Remove direct FastAPI calls to OpenRouter and TypeSafe, or leave only
  deterministic non-agent helpers with no model/provider dependency.
- [ ] Remove the product-specific Codex runner and gateway from the supported
  runtime: server.mjs, codex.mjs, runtime/bin/coffee.mjs, the sidecar
  service, and its startup/auth wiring.
- [ ] Decide whether jobs, messages, and meta remain as minimal UI,
  idempotency, or receipt projections. They must not schedule agent work,
  select native sessions, rebuild history, or become a second source of truth.
- [ ] Update README.md, PUBLICATION_SCOPE.md, docs/PERSONAL_PROFILE.md,
  SECURITY.md, AGENTS.md, and principles.md so the documented ownership
  matches the native Ez architecture.
- [ ] Search the complete tree and runtime configuration for direct provider
  URLs, raw Codex invocation, private launcher workarounds, and obsolete AI
  environment variables; classify each remaining occurrence.
- [ ] Run focused contract tests, frontend build, isolated-Mongo tests, plugin
  checks, and the real Ez smoke stories before deployment.
- [ ] Keep the previous private runtime and data available for rollback until
  personal and hosted acceptance is complete; do not delete it as part of a
  local documentation or code change.
- [ ] Deploy only after maintainer approval, then verify the deployed native Ez
  path and canonical readback. Do not treat container health alone as proof.
- [ ] Retire the legacy AI path only after every supported user/profile has
  accepted the replacement and the rollback window has closed.

QA: no enabled profile can answer or mutate through a direct provider, raw
Codex sidecar, or host process. A real native Ez turn produces the user-visible
reply, an authorized plugin receipt for each mutation, and the same canonical
record on API/UI readback. Self-host remains functional with chat and AI off.

## Per-feature approval

Before moving to the next checkbox group, provide:

- the feature(s) completed;
- a short live native-Ez QA walkthrough with canonical readback;
- what is intentionally WIP, replaced, or retired;
- any known blocker; and
- the one next group requesting approval.
