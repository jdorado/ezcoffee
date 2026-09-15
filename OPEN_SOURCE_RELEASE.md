# Open-source release gate

Publication and hosted deployment were approved by the maintainer on
2026-09-15. Checks remain evidence gates, not paperwork.

## Automated checks

- [x] `npm run build`
- [x] `npm --prefix coffee_app audit --omit=dev --omit=optional`
- [x] `uvx pip-audit -r coffee_api/requirements.txt`
- [x] `npm test`
- [x] `docker compose config`
- [x] `docker compose build`
- [x] Fresh self-host startup reaches `/health` and the browser UI.
- [x] Chat, sign-in, and personal equipment defaults are absent in self-host mode.
- [x] Create, edit, repeat, archive, restore, and delete work with fresh data.
- [x] Restart preserves the Docker volume data.

## Hosted production

- [x] Every hosted read and mutation is scoped by the verified Privy subject.
- [x] Automated two-user isolation covers coffee, shot, and profile access.
- [x] Hosted mode fails closed without authentication and rejects private AI.
- [ ] `ezcoffee.space` serves the Vercel production build from `main`.
- [ ] `api.ezcoffee.space` reaches only the loopback-bound VM API through TLS.
- [ ] Privy permits the production origin and a new user can sign up and log out.
- [ ] Signed-in create, edit, repeat, archive, restore, and delete pass in production.
- [ ] A second production account cannot read or mutate the first account's data.

## Personal regression

- [ ] The ignored frontend profile still shows the configured equipment and Chat.
- [ ] The personal API still requires the configured owner identity in production.
- [ ] A real chat write returns a canonical receipt and appears after readback.
- [ ] No personal deployment or production data is changed during self-host QA.

## Publication review

- [x] Review the current tracked tree for secrets, personal data, private URLs,
      absolute host paths, and machine-specific image or volume names.
- [x] Review dependency audit results and document any accepted risk.
- [x] Resolve or explicitly accept advisories in the optional personal
      Privy/wallet and development toolchains. The dependencies shipped in the
      self-host runtime currently pass their focused audit.
- [x] Start from a clean history that excludes the private repository's old
      infrastructure URLs and deployment paths.
- [ ] Confirm the MIT license and public repository name.
- [x] Obtain explicit maintainer approval before pushing, creating a public
      repository, and deploying the hosted service.

## Evidence after approval

- [ ] Read back public repository visibility, default branch, and license.
- [ ] Confirm CI passes on the exact public commit.
- [ ] Clone into a fresh directory and complete the README quick start.
- [ ] Record the public commit SHA and release URL.

## Dependency review notes

- The production npm audit with development and optional packages omitted is
  clean, and the Python audit reports no known vulnerabilities.
- `copy-webpack-plugin` was upgraded to remove its vulnerable serializer.
- The full npm graph still reports upstream advisories through Privy's optional
  wallet transports and the local webpack development server. ezcoffee enables
  only email and Google login, not wallet login; the deployed backend contains
  none of these JavaScript packages. This release accepts that bounded client
  risk while retaining the established Privy client, and CI continues to gate
  the production dependency set.
