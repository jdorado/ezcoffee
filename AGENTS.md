# Coffee Logbook contributor notes

Keep the product small: React/TypeScript, FastAPI, and MongoDB, with two records
only—coffees and shots. The public `selfhost` profile has no auth, billing, or AI.
Private deployment capabilities must stay opt-in and profile-driven.
Hosted AI uses the private Ezenciel CLI bridge; credentials stay API-only.
The bridge owns supported model/effort combinations and native structured output.

Mongo coffees and shots are canonical and revisioned. Reject stale edits. Do
not persist browser snapshots as data: the only browser copy is the read-only
startup cache in `stateSnapshot.ts`, which paints the first screen, is replaced
by every load, is tied to one account and build, and is cleared on sign-out.
Never write from it. Recipe reuse copies inputs only, never measured
outputs or tasting results. Planned tests are not logged shots.

The initial HTML shows the account-free coffee splash before JavaScript loads;
it disappears as soon as the app is ready, without a minimum display time.
Keep session confirmation ahead of all personal data, including the startup cache.

Keep real coffee data and all credentials in ignored files. Tests must use an
isolated database. Bind local defaults to loopback. Do not weaken authentication
in the personal profile.

Preserve the minimalist black-and-white UI and dense shot rows. Avoid adding
dashboards or new product areas without an explicit scope change.

Work directly on `main` for this repo. Keep testing minimal and proportional to
the change: run a relevant focused check when useful and build the frontend for
frontend changes. API tests must use an isolated Mongo instance. Push
automatically after each committed change, without waiting to be asked: push
`main` to `origin` (this triggers the existing deployment workflow), or the
session's designated branch when one is given. Do not separately publish,
change repository visibility, or deploy by other means without explicit
authorization.
