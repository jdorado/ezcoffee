#!/usr/bin/env bash
set -euo pipefail
set -m
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
pids=()
cleanup(){ for pid in ${pids[@]:-}; do kill -- "-$pid" 2>/dev/null || true; done; }
trap cleanup INT TERM HUP EXIT
if [[ -z "${MONGO_URL:-}" ]]; then
  FROM_ENV_FILE="$(grep -E '^\s*MONGO_URL\s*=' "$ROOT_DIR/.env" 2>/dev/null | tail -n 1 | cut -d= -f2- | tr -d ' "\"' || true)"
  if [[ -n "$FROM_ENV_FILE" ]]; then
    export MONGO_URL="$FROM_ENV_FILE"
  fi
fi
if [[ -z "${MONGO_URL:-}" ]]; then
  mkdir -p data/mongo
  mongod --dbpath "$ROOT_DIR/data/mongo" --bind_ip 127.0.0.1 --port 27019 --logpath "$ROOT_DIR/data/mongo.log" &
  pids+=("$!")
fi
for port in 8001 5176; do
  stale="$(lsof -ti :"$port" 2>/dev/null || true)"
  if [[ -n "$stale" ]]; then
    echo "Releasing port $port from stale process(es): $stale" >&2
    kill $stale 2>/dev/null || true
    for _ in {1..25}; do
      lsof -ti :"$port" >/dev/null 2>&1 || break
      sleep 0.2
    done
    if lsof -ti :"$port" >/dev/null 2>&1; then
      echo "Port $port is still in use. Stop it manually: lsof -i :$port" >&2
      exit 1
    fi
  fi
done
(cd coffee_api && .venv/bin/python -m uvicorn src.main:app --host 127.0.0.1 --port 8001) &
pids+=("$!")
npm --prefix coffee_app run dev &
pids+=("$!")
while true; do
 for pid in "${pids[@]}"; do kill -0 "$pid" 2>/dev/null || exit 1; done
 sleep 1
done
