#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_DIR/backend"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt

cd "$REPO_DIR/frontend"
npm install
npm run build

install -m 0644 "$REPO_DIR/deploy/systemd/greenhouse-backend.service" /etc/systemd/system/greenhouse-backend.service
install -m 0644 "$REPO_DIR/deploy/systemd/greenhouse-frontend.service" /etc/systemd/system/greenhouse-frontend.service

systemctl daemon-reload
systemctl enable greenhouse-backend.service
systemctl enable greenhouse-frontend.service
systemctl restart greenhouse-backend.service
systemctl restart greenhouse-frontend.service

systemctl --no-pager --full status greenhouse-backend.service greenhouse-frontend.service
