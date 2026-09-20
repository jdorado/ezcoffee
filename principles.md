# Coffee Logbook principles

## Project-specific principles

- Keep the product small: coffees and shots, not a general platform.
- Mongo records are canonical and revisioned; reject stale edits.
- Keep the public self-hosted profile simple and private capabilities opt-in.
- Preserve the dense minimalist interface.

## Agent architecture

- Ez owns agent sessions, context, reasoning, model/provider selection, tool
  choice, continuation, and any agent channel delivery.
- The coffee application owns authentication, account scope, canonical coffees
  and shots, deterministic validation, and the human UI.
- The installed EzCoffee plugin is the only execution surface: deterministic
  typed JSON over stdin, idempotent `--request-id`, `--expected-revision` for
  revisions, canonical receipts, no credentials or account identifiers in
  artifacts. No model loop, prompt builder, transcript replay, scheduler,
  database authority, or product-specific agent runner inside the plugin.
- No supported profile answers or mutates through a direct provider call, raw
  sidecar, host process, or application-owned orchestration path. Direct
  provider and sidecar code below are migration sources to retire, never to
  build on.
- Every mutation needs an idempotent request key where applicable, a canonical
  receipt, and readback before success is claimed.

## Coding flow

- Local change → simple focused verification → deploy `main` → verify the deployed result.

## Architecture and design constraints

- Keep the product as React/TypeScript, FastAPI and MongoDB with two canonical record types: coffees and shots.
- Mongo records are canonical and revisioned; reject stale edits and never persist browser snapshots as authority.
- The public `selfhost` profile has no auth, billing or AI; private capabilities remain opt-in and profile-driven, and every AI profile fails closed when Ez is unavailable or unbound.
- Keep real coffee data and all credentials in ignored files. Tests and local development use an isolated database, never production. Bind local defaults to loopback.
- Use isolated test data and require explicit approval before publication or deployment.
