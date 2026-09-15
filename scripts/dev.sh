#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
pids=()
cleanup(){ for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done; }
trap cleanup INT TERM EXIT
if [[ -z "${MONGO_URL:-}" ]]; then
 mkdir -p data/mongo
 mongod --dbpath "$ROOT_DIR/data/mongo" --bind_ip 127.0.0.1 --port 27019 --logpath "$ROOT_DIR/data/mongo.log" &
 pids+=("$!")
fi
(cd coffee_api && .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8001) &
pids+=("$!")
node coffee_api/coffee_ai/server.mjs &
pids+=("$!")
npm --prefix coffee_app run dev &
pids+=("$!")
while true; do
 for pid in "${pids[@]}"; do kill -0 "$pid" 2>/dev/null || exit 1; done
 sleep 1
done
