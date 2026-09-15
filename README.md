# ezcoffee

A small, self-hosted coffee journal for tracking coffees, recipes, tasting
notes, and dial-in experiments. The default open-source profile is a private
single-user app on your own machine: no signup, billing, analytics, or AI.

## Features

- Create and archive coffees without losing their shot history.
- Log, edit, repeat, lock, and delete espresso shots.
- Keep actual results separate from planned next tests.
- Track recipe inputs, output, timing, taste, ratings, and roast windows.
- Reject stale edits with revision checks.
- Adapt the brew form from the Profile tab: choose a Lelit Mara X, generic
  espresso, standard pour-over, or custom setup, then show, hide, and order the
  fields you care about.

The standard pour-over preset covers water temperature and quantity, optional
ice, coffee dose and computed ratio, grind size, total and bloom time, coffee
brand, taste, and rating. The profile is stored in MongoDB with revision checks;
it is not tied to one developer's machine.

## Quick start

You need Docker with Compose v2.

```sh
git clone https://github.com/jdorado/ezcoffee.git
cd ezcoffee
cp .env.example .env
docker compose up -d --build --wait
```

Open <http://127.0.0.1:5176>. Data is stored in the `mongo_data` Docker volume.
To stop the app without deleting data, run `docker compose down`.

The default bind is loopback-only. If you expose the app to a network, put it
behind authentication and HTTPS first; the self-host profile intentionally has
no accounts or access control.

## Your profile

Edit the untracked `.env` file to set the local port, equipment label, and new
shot defaults. Empty values are valid and keep the public defaults generic.
See [.env.example](.env.example) for every supported setting.

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

## Local development

Requires Node.js, Python 3.11+, and MongoDB. The development helper expects a
Python virtual environment at `coffee_api/.venv` and starts its own loopback
Mongo process when `MONGO_URL` is not set.

```sh
npm --prefix coffee_app install
python3 -m venv coffee_api/.venv
coffee_api/.venv/bin/pip install -r coffee_api/requirements.txt
cp coffee_app/.env.example coffee_app/.env.local
npm run dev
```

Frontend: <http://127.0.0.1:5176>. API: <http://127.0.0.1:8001>.

```sh
npm run build
npm test
```

Tests use an isolated Mongo database and must never point at personal records.

## Profiles and roadmap

- `selfhost` is the public default and includes only Shots.
- `personal` is an opt-in migration profile. The existing private repository
  remains the production source of truth until each private capability is
  deliberately migrated and accepted here.
- Multi-account hosted signup, subscriptions, and hosted AI are future phases;
  they are not claimed by this release.

The private profile is documented in
[docs/PERSONAL_PROFILE.md](docs/PERSONAL_PROFILE.md). Product scope and staged
release boundaries are in [PUBLICATION_SCOPE.md](PUBLICATION_SCOPE.md).

## License

ezcoffee is available under the [MIT License](LICENSE).
