#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE_FILE="${COFFEE_DEPLOY_PROFILE:-$ROOT_DIR/profiles/deploy.env}"
if [[ ! -f "$PROFILE_FILE" ]]; then
  echo "Missing deploy profile: $PROFILE_FILE (copy profiles/deploy.env.example)." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$PROFILE_FILE"
set +a
: "${COFFEE_VM_TARGET:?Set COFFEE_VM_TARGET in the deploy profile}"
: "${COFFEE_REMOTE_DIR:?Set COFFEE_REMOTE_DIR in the deploy profile}"
: "${COFFEE_REMOTE_PROFILE:?Set COFFEE_REMOTE_PROFILE in the deploy profile}"
: "${COFFEE_HEALTH_URL:?Set COFFEE_HEALTH_URL in the deploy profile}"
cd "$ROOT_DIR"
# Runtime credentials, database exports, and CLI state are provisioned separately.
rsync -az --exclude .git --exclude node_modules --exclude .venv --exclude dist \
  --exclude .vercel --exclude '.env*' --exclude __pycache__ --exclude data \
  ./ "$COFFEE_VM_TARGET:$COFFEE_REMOTE_DIR/"
ssh "$COFFEE_VM_TARGET" bash -s -- "$COFFEE_REMOTE_DIR" "$COFFEE_REMOTE_PROFILE" <<'REMOTE'
set -euo pipefail
cd "$1"
sudo docker compose --env-file "$2" -f compose.personal.yml up -d --build --wait --remove-orphans
REMOTE
curl --fail --silent --show-error "$COFFEE_HEALTH_URL"
