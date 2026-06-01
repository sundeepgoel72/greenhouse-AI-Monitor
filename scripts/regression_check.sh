#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8088}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:5173}"

cd "$ROOT_DIR"

wait_for_url() {
  local name="$1"
  local url="$2"
  local attempts="${3:-20}"

  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name ready"
      return 0
    fi
    sleep 1
  done

  echo "$name did not become ready: $url" >&2
  return 1
}

echo "Backend regression tests"
backend/.venv/bin/python -m pytest backend/tests

echo "Frontend production build"
(
  cd frontend
  npm run build
)

echo "Readiness checks"
wait_for_url "Backend" "$BACKEND_URL/api/health"
wait_for_url "Frontend" "$FRONTEND_URL/"

echo "HTTP smoke checks"
BACKEND_URL="$BACKEND_URL" FRONTEND_URL="$FRONTEND_URL" scripts/smoke_check.sh

echo "Backend UI config"
curl -fsS "$BACKEND_URL/api/config"
echo

echo "Recent sensor readings"
curl -fsS "$BACKEND_URL/api/sensor-readings?limit=2"
echo

echo "Systemd service status"
systemctl --no-pager --quiet is-active greenhouse-backend.service
systemctl --no-pager --quiet is-active greenhouse-frontend.service
echo "ok"
