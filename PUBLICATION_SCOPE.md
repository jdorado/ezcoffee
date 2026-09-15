# Coffee Logbook public side project

## Goal

Publish the app for coffee aficionados in two ways:

1. **Self-hosted:** free and open source, with the Shots logbook and no AI.
2. **Hosted:** sign up and use Shots for free. AI has a 7-day free trial and
   then requires one annual Stripe subscription.

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

Vercel and Mongo can start free. The domain, Stripe fees, and AI usage are still
costs, so the annual plan needs a reasonable AI usage limit.

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
- Free users get the complete Shots product without AI.

### 3. AI trial and annual plan

- Add one annual Stripe subscription with a 7-day trial.
- Start the trial only when the user chooses AI and enters payment details.
- Use Stripe webhooks as the source of subscription status.
- Enable AI only for trialing or active accounts and within the usage limit.
- If the trial ends or the user cancels, disable AI but keep all coffees and
  shots available on the free plan.
- Use one hosted model/provider path. OpenRouter with a selected model is one
  option; test it before committing to it.

## Release order

1. Publish the self-hosted Shots app.
2. Launch hosted signup with free Shots.
3. Add the AI trial and annual subscription.

None of these steps requires migrating or changing my personal app.

## Done when

- A new user can self-host the Shots app from the README.
- Two hosted users cannot see or change each other's data.
- A hosted user can use Shots free, start the 7-day AI trial, subscribe annually,
  cancel, and keep their non-AI logbook.
- The personal app still works unchanged.

## Current release gate

- The self-hosted and free hosted profiles are in release verification.
- Public name: ezcoffee.
- License: MIT.

## Decisions left for AI phases

- Annual price and AI usage limit.
- Hosted model/provider.
