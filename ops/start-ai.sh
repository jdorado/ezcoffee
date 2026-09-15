#!/bin/sh
set -eu
install -d -m 0700 -o 10001 -g 10001 /srv/coffee/home /srv/coffee/codex-home /srv/coffee/workspace
install -d -m 0755 /srv/coffee/runtime/bin
install -m 0444 /opt/coffee/coffee.mjs /srv/coffee/runtime/bin/coffee.mjs
install -m 0444 /opt/coffee/AGENTS.md /srv/coffee/workspace/AGENTS.md
if [ "${COFFEE_SHARE_CODEX_AUTH:-0}" = "1" ]; then
 if [ ! -f /run/shared-codex/auth.json ]; then
  echo "Shared Codex authentication is unavailable" >&2
  exit 1
 fi
 rm -f /srv/coffee/codex-home/auth.json
 ln -s /run/shared-codex/auth.json /srv/coffee/codex-home/auth.json
elif [ ! -f /srv/coffee/codex-home/auth.json ]; then
 install -m 0600 -o 10001 -g 10001 /run/shared-codex/auth.json /srv/coffee/codex-home/auth.json
fi
printf 'model = "%s"\nmodel_reasoning_effort = "%s"\n' \
 "${CODEX_MODEL:-gpt-5.6-sol}" "${CODEX_REASONING_EFFORT:-medium}" \
 > /srv/coffee/codex-home/config.toml
chown 10001:10001 /srv/coffee/codex-home/config.toml
chmod 0600 /srv/coffee/codex-home/config.toml
exec setpriv --reuid=10001 --regid=10001 --init-groups node /coffee/server.mjs
