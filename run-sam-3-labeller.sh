#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
BACKEND_DIR="$REPO_ROOT/labeler_app/backend"
FRONTEND_DIR="$REPO_ROOT/labeler_app/frontend"

echo "[labeler] running preflight checks from $REPO_ROOT"

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[labeler] backend directory not found: $BACKEND_DIR" >&2
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "[labeler] frontend directory not found: $FRONTEND_DIR" >&2
  exit 1
fi

echo "[labeler] syncing backend dependencies with uv"
cd "$BACKEND_DIR"
uv sync >/dev/null

echo "[labeler] starting FastAPI server for health check"
uv run uvicorn app.main:app --host 127.0.0.1 --port 8123 --log-level warning >/tmp/labeler-backend.log 2>&1 &
BACKEND_PID=$!
trap 'kill $BACKEND_PID >/dev/null 2>&1 || true' EXIT

echo "[labeler] waiting for server..."
for i in {1..20}; do
  if curl -fsS http://127.0.0.1:8123/health >/dev/null 2>&1; then
    echo "[labeler] backend health check passed"
    break
  fi
  sleep 0.3
  if [[ $i -eq 20 ]]; then
    echo "[labeler] backend failed to start, see /tmp/labeler-backend.log" >&2
    exit 1
  fi
done

echo "[labeler] running frontend build"
cd "$FRONTEND_DIR"
npm install >/dev/null
npm run build >/dev/null
echo "[labeler] frontend build passed"

kill $BACKEND_PID >/dev/null 2>&1 || true
trap - EXIT

echo "[labeler] all checks passed"

