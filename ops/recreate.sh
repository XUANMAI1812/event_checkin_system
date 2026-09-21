#!/usr/bin/env bash
# Chay tren EC2: bash ops/recreate.sh <ten-service>
# Khong dung `docker compose up -d` tran cho ca stack. No keo moi service ve
set -euo pipefail
svc="${1:?Dung: bash ops/recreate.sh <ten-service>}"
PROJECT="${COMPOSE_PROJECT:-event_checkin_system}"
cd "$(dirname "${BASH_SOURCE[0]}")/.."

cid=$(docker ps -aq \
  --filter "label=com.docker.compose.project=$PROJECT" \
  --filter "label=com.docker.compose.service=$svc" | head -n 1)
if [ -z "$cid" ]; then
  echo "Khong thay container cua '$svc' (project $PROJECT)."
  exit 1
fi

image=$(docker inspect -f '{{.Config.Image}}' "$cid")
tag="${image##*:}"
echo "$svc dang chay $image: giu nguyen tag '$tag'"

IMAGE_TAG="$tag" docker compose -f docker-compose.prod.yml up -d --no-deps "$svc"
docker compose -f docker-compose.prod.yml ps "$svc"
