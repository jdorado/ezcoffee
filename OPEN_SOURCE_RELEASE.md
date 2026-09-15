# Open-source release gate

Publication is intentionally paused until maintainer QA is complete.

## Automated checks

- [ ] `npm run build`
- [ ] `npm --prefix coffee_app audit --omit=dev --omit=optional`
- [ ] `uvx pip-audit -r coffee_api/requirements.txt`
- [ ] `npm test`
- [ ] `docker compose config`
- [ ] `docker compose build`
- [ ] Fresh self-host startup reaches `/health` and the browser UI.
- [ ] Chat, sign-in, and personal equipment defaults are absent in self-host mode.
- [ ] Create, edit, repeat, archive, restore, and delete work with fresh data.
- [ ] Restart preserves the Docker volume data.

## Personal regression

- [ ] The ignored frontend profile still shows the configured equipment and Chat.
- [ ] The personal API still requires the configured owner identity in production.
- [ ] A real chat write returns a canonical receipt and appears after readback.
- [ ] No personal deployment or production data is changed during self-host QA.

## Publication review

- [ ] Review the current tracked tree for secrets, personal data, private URLs,
      absolute host paths, and machine-specific image or volume names.
- [ ] Review dependency audit results and document any accepted risk.
- [ ] Resolve or explicitly accept advisories in the optional personal
      Privy/wallet and development toolchains. The dependencies shipped in the
      self-host runtime currently pass their focused audit.
- [x] Start from a clean history that excludes the private repository's old
      infrastructure URLs and deployment paths.
- [ ] Confirm the MIT license and public repository name.
- [ ] Obtain explicit maintainer approval after QA before pushing, changing
      visibility, creating a public repository, or publishing a release.

## Evidence after approval

- [ ] Read back public repository visibility, default branch, and license.
- [ ] Confirm CI passes on the exact public commit.
- [ ] Clone into a fresh directory and complete the README quick start.
- [ ] Record the public commit SHA and release URL.
