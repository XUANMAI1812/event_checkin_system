#!/usr/bin/env bash
# Chay tren EC2: bash ops/sync.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

ENV_FILE=/etc/event-checkin-watcher.env
if [ ! -f "$ENV_FILE" ]; then
  echo "Thieu $ENV_FILE - tao tu ops/watcher/watcher.env.example truoc (muc 8.3)."
  exit 1
fi

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "Working tree co thay doi chua commit, dung lai (khong git pull):"
  git status --short --untracked-files=no
  exit 1
fi

git pull --ff-only
docker compose -f docker-compose.prod.yml config -q

sudo install -m 755 ops/watcher/watcher.sh /usr/local/bin/event-checkin-watcher
sudo install -m 644 ops/watcher/event-checkin-watcher.service /etc/systemd/system/event-checkin-watcher.service
sudo systemctl daemon-reload
sudo systemctl enable event-checkin-watcher >/dev/null 2>&1
sudo systemctl restart event-checkin-watcher

echo "Da dong bo. Commit dang chay tren EC2: $(git rev-parse --short HEAD)"
echo "Watcher: $(systemctl is-active event-checkin-watcher)"
