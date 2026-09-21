<p align="center">
  <img src="coffee_app/public/ezcoffee-logo-header.png" alt="ezcoffee" width="300">
</p>

<p align="center">
  <strong>An open-source coffee journal for dialing in espresso and pour-over.</strong>
</p>

<p align="center">
  Track beans once, log every brew, compare what changed, and keep the recipes
  worth repeating.
</p>

<p align="center">
  <a href="https://ezcoffee.space"><strong>Try ezcoffee</strong></a>
  ·
  <a href="#run-it-yourself">Run it yourself</a>
  ·
  <a href="#what-you-can-track">Features</a>
</p>

<p align="center">
  <a href="https://github.com/jdorado/ezcoffee/actions/workflows/ci.yml"><img src="https://github.com/jdorado/ezcoffee/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-222222.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/self--host-Docker-555555.svg" alt="Self-host with Docker">
</p>

## Your coffee, with a memory

Great coffee is iterative. A grind adjustment, a hotter brew, a longer bloom,
or a different ratio can turn the same beans into a different cup—but only if
you remember what happened last time.

ezcoffee is a focused brew log for coffee enthusiasts. It keeps beans,
espresso shots, pour-over brews, recipes, tasting notes, and planned experiments
in one quiet, installable web app. There are no feeds, leaderboards, or
gamification: just a useful record of how you brewed and what you enjoyed.

The brew form adapts to your setup. Start with a Lelit Mara X, a generic
espresso machine, standard pour-over, or a custom profile. Then choose which
fields appear and the order in which you record them.

## What you can track

### Espresso

- Dose, yield, ratio, grind size, brew time, and first drip.
- Pressure, basket, paper filter, puck screen, and temperature or PID setting.
- Planned next tests kept separate from completed shots.
- One-click recipe reuse without copying measured results or tasting notes.
- Dialed-in recipe locks, roast windows, taste balance, outcome, and rating.

### Pour-over and filter coffee

- Coffee dose, water quantity, and automatically calculated brew ratio.
- Water temperature, grind size, total brew time, and bloom time.
- Optional ice quantity for iced pour-over.
- Taste notes, result, and enjoyment rating.

### Coffee library

- Coffee name, roaster or brand, roast date, origin, process, and notes.
- Brew history stays attached when a finished bag is archived.
- Canister markers make several coffees easy to tell apart on the bar.

All records are revisioned so a stale edit cannot silently overwrite a newer
one. Coffee details are stored once per coffee; profile settings only decide
which brew fields you want to see.

## Use the hosted app

[ezcoffee.space](https://ezcoffee.space) is the free hosted version. Sign in
with Privy and your coffees, brews, and profile remain scoped to your verified
account.

The hosted profile also supports a small coffee assistant for every registered
user. It can discuss the selected coffee using your profile and a bounded
snapshot of recent brews. When explicitly asked, it can propose coffee or brew
creates and updates; the authenticated API applies them through the same
account, revision, and field validation as the forms. The model receives no
database credentials or direct write token and cannot see another account.

Hosted AI is configuration-gated and fails closed when it is not enabled.

## Run it yourself

The open-source edition is free, local-first to operate, and does not require an
account or AI provider. You need Docker with Compose v2.

```sh
git clone https://github.com/jdorado/ezcoffee.git
cd ezcoffee
cp .env.example .env
docker compose -f compose.yml -f compose.local.yml up -d --build --wait
```

Open [http://127.0.0.1:5176](http://127.0.0.1:5176). Your data is stored in the
`mongo_data` Docker volume.

```sh
docker compose -f compose.yml -f compose.local.yml down
```

Stopping the stack does not delete the volume or your coffee data. The default
bind is loopback-only. If you expose ezcoffee to a network, add authentication
and HTTPS first: the self-host profile is intentionally anonymous.

### Make the journal yours

Use the Profile tab to select a brew-method preset, name your equipment, and
show, hide, or reorder tracked fields. You can also seed local defaults in the
untracked `.env` file:

```dotenv
ESPRESSO_MACHINE_LABEL=My espresso machine
GRINDER_LABEL=My grinder
DEFAULT_DOSE_G=18
DEFAULT_GRIND=12
DEFAULT_BASKET=Double basket
DEFAULT_PAPER=no
DEFAULT_TEMP=I
DEFAULT_PUCK_SCREEN=yes
```

See [.env.example](.env.example) for the supported settings. Empty values keep
the public defaults generic.

## Install it as an app

ezcoffee is a Progressive Web App (PWA). Open **Profile → Install ezcoffee**:
compatible Android and desktop browsers open their native install dialog, while
Safari shows the exact **Add to Home Screen** or **Add to Dock** steps. The
option disappears after installation.

The service worker provides a safe offline reconnect page; coffee records remain
server-backed and are not copied into an offline browser cache.

## How it works

```text
React + TypeScript PWA
          │
       FastAPI
          │
        MongoDB
```

The project deliberately stays small: one frontend, one API, and MongoDB as the
canonical record store. Hosted authentication and coffee chat are optional
profiles, not requirements for self-hosting.

| Profile | Intended use | Authentication | Coffee assistant |
| --- | --- | --- | --- |
| `selfhost` | Your own local installation | None by default | Off |
| `hosted` | Free multi-user service | Privy | OpenRouter for every registered user |
| `personal` | Maintainer's private deployment | Owner-only Privy | OpenRouter |

## Local development

You need Node.js, Python 3.11+, and MongoDB. The development helper expects a
Python virtual environment at `coffee_api/.venv` and starts a loopback Mongo
process when `MONGO_URL` is not set.

```sh
npm --prefix coffee_app install
python3 -m venv coffee_api/.venv
coffee_api/.venv/bin/pip install -r coffee_api/requirements.txt
cp coffee_app/.env.example coffee_app/.env.local
npm run dev
```

Frontend: [http://127.0.0.1:5176](http://127.0.0.1:5176). API:
[http://127.0.0.1:8001](http://127.0.0.1:8001).

```sh
npm run build
npm test
```

Tests use an isolated Mongo database and must never point at personal records.
Authenticated local development fails closed when Privy is not configured;
there is no anonymous fallback for the hosted or personal profiles.

## Production and hosted deployment

There are two environments: local and production. Production secrets belong in
a protected file outside the checkout—never in Git, browser code, Vercel build
variables intended for clients, or Compose examples.

The hosted frontend deploys from `coffee_app` on Vercel. The FastAPI service is
deployed from [compose.hosted.yml](compose.hosted.yml), bound to loopback on its
VM, and exposed through an HTTPS reverse proxy. Every push to `main` must pass
CI before the exact commit is deployed.

For a production self-host, provide Mongo through your own protected runtime
environment:

```sh
sudo install -d -m 700 /etc/ezcoffee
sudo install -m 600 profiles/production.env.example /etc/ezcoffee/production.env
# Edit /etc/ezcoffee/production.env with the real MONGO_URL.
docker compose --env-file /etc/ezcoffee/production.env -f compose.yml up -d --build --wait
```

Hosted chat uses OpenRouter's `~z-ai/glm-flash-latest` alias with structured
outputs required and provider fallback enabled. Operators keep
`OPENROUTER_API_KEY` in the protected API runtime environment. The browser
never receives it. See
[profiles/hosted.env.example](profiles/hosted.env.example) for placeholders and
[PUBLICATION_SCOPE.md](PUBLICATION_SCOPE.md) for the release boundaries.

The maintainer-only migration profile is documented separately in
[docs/PERSONAL_PROFILE.md](docs/PERSONAL_PROFILE.md).

## Contributing

Bug reports, focused improvements, and support for more coffee equipment or
brew workflows are welcome. Keep contributions aligned with the project's
small architecture and minimalist black-and-white interface. Please run
`npm test` and `npm run build` before opening a pull request.

Useful areas to improve include:

- Espresso and filter-coffee tracking workflows.
- Equipment presets that stay generic and machine-independent.
- Accessibility and mobile/PWA behavior.
- Import and export formats that preserve record ownership and history.
- Documentation for new self-hosters.

## FAQ

### Is ezcoffee only for espresso?

No. It includes tailored tracking for espresso, pour-over, iced pour-over, and
custom brew setups.

### Do I need an AI key?

No. The self-hosted coffee journal works without AI. The hosted service uses
its own server-side OpenRouter key for registered users.

### Can I use SQLite instead of MongoDB?

Not currently. MongoDB is the canonical store for both local and hosted
profiles, which keeps behavior and revision checks consistent.

### Is this a coffee inventory or café POS system?

No. ezcoffee is a personal coffee journal and brew tracker for learning from
your own espresso shots and filter brews.

## License

ezcoffee is open source under the [MIT License](LICENSE).
