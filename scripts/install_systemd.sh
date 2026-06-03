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

sed "s|__REPO_DIR__|$REPO_DIR|g" "$REPO_DIR/deploy/systemd/greenhouse-backend.service" | sudo tee /etc/systemd/system/greenhouse-backend.service >/dev/null
sed "s|__REPO_DIR__|$REPO_DIR|g" "$REPO_DIR/deploy/systemd/greenhouse-frontend.service" | sudo tee /etc/systemd/system/greenhouse-frontend.service >/dev/null

systemctl daemon-reload
systemctl enable greenhouse-backend.service
systemctl enable greenhouse-frontend.service
systemctl restart greenhouse-backend.service
systemctl restart greenhouse-frontend.service

systemctl --no-pager --full status greenhouse-backend.service greenhouse-frontend.service
