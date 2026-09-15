# Security

The default self-host profile binds to `127.0.0.1` and has no authentication.
Do not expose it directly to the internet or an untrusted network. Put it behind
HTTPS and an authentication layer if remote access is required.

Keep `.env` files, database exports, personal records, API keys, and AI
credentials out of the repository. If you discover a vulnerability, report it
privately to the repository owner instead of opening a public issue with exploit
details or secrets.
