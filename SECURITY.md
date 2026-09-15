# Security

The default self-host profile binds to `127.0.0.1` and has no authentication.
Do not expose it directly to the internet or an untrusted network. Put it behind
HTTPS and an authentication layer if remote access is required.

Keep `.env` files, database exports, personal records, API keys, and AI
credentials out of the repository. If you discover a vulnerability, report it
privately to the repository owner instead of opening a public issue with exploit
details or secrets.

The hosted profile requires a valid Privy access token on every user endpoint.
Mongo records are tagged with the verified Privy subject and every read and
mutation includes that account boundary. The API is bound to loopback on the
production VM and exposed only through HTTPS. Hosted AI is deliberately disabled;
the maintainer's private Codex credentials and sessions are never deployed.

Production secrets belong in Vercel, GitHub Actions, or a mode-0600 runtime file
outside the VM checkout. Rotate a credential immediately if it appears in an
issue, log, commit, or pull request.
