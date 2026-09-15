# Personal profile

The personal profile is a migration bridge for the maintainer's existing
owner-authenticated AI deployment without making any machine, account,
credential, or live URL part of the public defaults. The original private
repository remains authoritative until a capability is deliberately migrated
and accepted here.

It is not required for self-hosting and is not a supported hosted AI product.
The AI image must already contain a working Codex CLI installation.

## Runtime configuration

1. Copy `profiles/personal.env.example` to an ignored file on the target host.
2. Fill in the private API environment path, credential seed directory, image,
   port, and volume names.
3. Keep the referenced API environment and credential seed outside this repo.

The API environment must provide `MONGO_URL` and Privy credentials plus
an exact `COFFEE_OWNER_SUB`. The browser build separately needs `APP_MODE=personal`,
`CHAT_ENABLED=true`, `PRIVY_APP_ID`, `API_BASE_URL`, and any desired equipment
defaults.

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
