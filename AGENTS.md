# Coffee Logbook contributor notes

Keep the product small: React/TypeScript, FastAPI, and MongoDB, with two records
only—coffees and shots. The public `selfhost` profile has no auth, billing, or AI.
Private deployment capabilities must stay opt-in and profile-driven.

Mongo coffees and shots are canonical and revisioned. Reject stale edits. Do
not persist browser snapshots. Recipe reuse copies inputs only, never measured
outputs or tasting results. Planned tests are not logged shots.

Keep real coffee data and all credentials in ignored files. Tests must use an
isolated database. Bind local defaults to loopback. Do not weaken authentication
in the personal profile.

Preserve the minimalist black-and-white UI and dense shot rows. Avoid adding
dashboards or new product areas without an explicit scope change.

Work directly on `main` for this repo. Keep testing minimal and proportional to
the change: run a relevant focused check when useful and build the frontend for
frontend changes. API tests must use an isolated Mongo instance. When the
maintainer says "push," push `main` to `origin`; this triggers the existing
deployment workflow. Do not push before that request, or separately publish,
change repository visibility, or deploy without explicit authorization.
