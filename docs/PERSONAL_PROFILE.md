# Personal profile

The personal profile is the maintainer's private, owner-authenticated
deployment. It shares the hosted AI backend (OpenRouter) and keeps every
machine, account, credential, and live URL out of the public defaults. The
original private repository remains authoritative until a capability is
deliberately migrated and accepted here.

It is not required for self-hosting and is not a supported hosted AI product.

## Runtime configuration

1. Copy `profiles/personal.env.example` to an ignored file on the target host.
2. Fill in the private API environment path, port, and database name.
3. Keep the referenced API environment file outside this repo.

The API environment must provide `MONGO_URL`, `OPENROUTER_API_KEY`, and Privy
credentials plus an exact `COFFEE_OWNER_SUB`. The browser build separately needs
`APP_MODE=personal`, `CHAT_ENABLED=true`, `PRIVY_APP_ID`, `API_BASE_URL`, and any
desired equipment defaults.

For local QA, those values may live together in the ignored root `.env` file.
Both the browser and API must use the same `PRIVY_APP_ID`; the secret is read by
the API only and is not part of the browser build's environment allowlist.

## Deployment configuration

Copy `profiles/deploy.env.example` to `profiles/deploy.env` locally. That ignored
profile owns the SSH target, remote directory, remote Compose profile path, and
health URL. Then run:

```sh
bash scripts/deploy.sh
```

Deployment is intentionally separate from the public self-host stack. Verify a
real signed-in read/write and an AI receipt after health checks; container health
alone does not prove the private user flow.
