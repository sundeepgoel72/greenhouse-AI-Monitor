#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8088}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:5173}"

echo "Backend health"
curl -fsS "$BACKEND_URL/api/health"
echo

echo "Beds"
curl -fsS "$BACKEND_URL/api/beds" >/dev/null
echo "ok"

echo "Latest snapshot"
curl -fsS "$BACKEND_URL/api/snapshots/latest" >/dev/null
echo "ok"

echo "Sensor readings"
curl -fsS "$BACKEND_URL/api/sensor-readings?limit=5" >/dev/null
echo "ok"

echo "Frontend"
curl -fsSI "$FRONTEND_URL/" >/dev/null
echo "ok"
