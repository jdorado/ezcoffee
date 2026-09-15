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

For frontend changes, run the focused frontend checks and
`npm --prefix coffee_app run build`. For API changes, run `npm test` with an
isolated Mongo instance. Do not publish, change repository visibility, deploy,
or push to a deployment branch until the maintainer has completed QA and
explicitly approved publication.
