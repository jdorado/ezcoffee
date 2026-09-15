# Coffee Logbook public side project

## Goal

Publish the app for coffee aficionados in two ways:

1. **Self-hosted:** free and open source, with the Shots logbook and no AI.
2. **Hosted:** sign up and use the complete product for free, including the
   coffee assistant. All registered users receive the same features.

My personal app stays as it is today: private Mongo data, owner login, and my
own Codex CLI. It does not need public signup or billing.

## Keep it simple

- Keep React, FastAPI, and Mongo.
- Use Mongo for both self-hosted and hosted versions. No SQLite.
- Host the public app on Vercel and use a free Mongo instance while within the
  free-tier limits.
- Keep one codebase with `APP_MODE=selfhost|hosted|personal`.
- Use one hosted AI provider, configured by server-side URL, model, and API key.
- Do not share my personal Codex CLI, session, credentials, or data with public
  users.

Vercel and Mongo can start free. The domain and AI usage are operating costs,
but there is no billing or per-user feature gate for now.

## What needs to be built

### 1. Open-source version

- Remove private URLs, data, credentials, and deployment settings.
- Add a license, simple README, `.env.example`, and Docker Compose setup.
- Default to no signup, no Stripe, and no Chat tab.
- Let users create/archive coffees and log, edit, repeat, and delete shots.

### 2. Hosted free version

- Reuse Privy signup.
- Create one account on first login.
- Add `account_id` to each coffee and shot and scope every request to that
  account.
- Deploy the app/API on Vercel using a separate public Mongo database.
- Registered users get the complete Shots product and coffee chat.

### 3. Hosted coffee assistant

- Use one OpenRouter call inside the existing authenticated FastAPI API.
- Build a bounded context from only that account's profile, selected coffee,
  recent brews, and short conversation history.
- Keep the provider key in the protected VM environment only.
- Keep inference input/output compact and use one lean model alias.
- Validate model-proposed record actions through the same account and revision
  rules as the forms; give the model no database credentials or direct write
  token.

## Release order

1. Publish the self-hosted Shots app.
2. Launch hosted signup with free Shots.
3. Enable hosted coffee chat after adding the protected server key and
   completing signed-in QA.

None of these steps requires migrating or changing my personal app.

## Done when

- A new user can self-host the Shots app from the README.
- Two hosted users cannot see or change each other's data.
- A hosted user can use Shots and bounded coffee chat for free without seeing
  another account's records.
- The personal app still works unchanged.

## Current release gate

- The self-hosted and free hosted profiles are in release verification.
- Public name: ezcoffee.
- License: MIT.

## Hosted AI operations

- Use `~deepseek/deepseek-v4-flash-latest` through OpenRouter initially.
- Keep billing out unless operating costs later justify a separate decision.
