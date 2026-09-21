#!/usr/bin/env bash
# Watcher: tu restart container app bi unhealthy, bao Telegram khi co su co
# Postgres/Redis/Mailpit va container da tat chi bi bao, khong tu restart

set -uo pipefail

PROJECT="${COMPOSE_PROJECT:-event_checkin_system}"
APP_SERVICES="${APP_SERVICES:-registration-service checkin-service notification-worker}"
DATA_SERVICES="${DATA_SERVICES:-postgres redis mailpit}"
POLL_INTERVAL="${POLL_INTERVAL:-30}"
MAX_RESTARTS="${MAX_RESTARTS:-3}"
RESTART_WINDOW="${RESTART_WINDOW:-900}"
DOWN_THRESHOLD="${DOWN_THRESHOLD:-2}"
DISK_ALERT_PERCENT="${DISK_ALERT_PERCENT:-85}"
MEM_ALERT_MB="${MEM_ALERT_MB:-80}"
HOST_ALERT_COOLDOWN="${HOST_ALERT_COOLDOWN:-3600}"
ALERT_PREFIX="${ALERT_PREFIX:-$(hostname)}"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

declare -A ALERTED=()         # da bao loi, chua hoi phuc
declare -A GAVE_UP=()         # het luot restart
declare -A DOWN_COUNT=()      # so vong lien tiep "down"
declare -A RESTART_LOG=()     # epoch cac lan restart gan day
declare -A LAST_HOST_ALERT=() # loai canh bao may chu -> epoch lan bao cuoi

CLS=""     # ket qua classify: ok, starting, unhealthy, down
DETAIL=""
RECENT=0   # ket qua prune restarts

log() { echo "$(date '+%F %T') $*"; }

send_telegram() {
  if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    log "Chua cau hinh Telegram, bo qua gui tin"
    return 0
  fi
  local code
  code=$(printf 'url = "https://api.telegram.org/bot%s/sendMessage"\n' "$TELEGRAM_BOT_TOKEN" \
    | curl -sS -m 10 -K - -o /dev/null -w '%{http_code}' \
        --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
        --data-urlencode "text=$1" 2>&1) || true
  [ "$code" = "200" ] || log "Gui Telegram that bai (ket qua: $code)"
}

alert() {
  log "ALERT: $1"
  send_telegram "[$ALERT_PREFIX] $1"
}

cooldown_alert() {
  local now last
  now=$(date +%s)
  last=${LAST_HOST_ALERT[$1]:-0}
  if (( now - last >= HOST_ALERT_COOLDOWN )); then
    LAST_HOST_ALERT[$1]=$now
    alert "$2"
  fi
}

container_id() {
  docker ps -aq \
    --filter "label=com.docker.compose.project=$PROJECT" \
    --filter "label=com.docker.compose.service=$1" | head -n 1
}

classify() {  # $1=svc -> CLS, DETAIL
  local cid status="" health="" exitcode=""
  cid=$(container_id "$1")
  if [ -z "$cid" ]; then
    CLS=down; DETAIL="khong co container"; return
  fi
  read -r status health exitcode < <(docker inspect -f \
    '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.State.ExitCode}}' \
    "$cid" 2>/dev/null) || true
  if [ "$status" = "running" ]; then
    case "$health" in
      unhealthy) CLS=unhealthy; DETAIL="HEALTHCHECK that bai lien tiep" ;;
      starting)  CLS=starting;  DETAIL="dang khoi dong" ;;
      *)         CLS=ok;        DETAIL="" ;;
    esac
  else
    CLS=down; DETAIL="status=${status:-khong ro} exit=${exitcode:-?}"
  fi
}

prune_restarts() {
  local kept="" t
  RECENT=0
  for t in ${RESTART_LOG[$1]:-}; do
    if (( $2 - t < RESTART_WINDOW )); then
      kept+="$t "
      RECENT=$(( RECENT + 1 ))
    fi
  done
  RESTART_LOG[$1]="$kept"
}

check_service() {  # $1=svc $2=app|data
  local svc=$1 kind=$2 now cid
  now=$(date +%s)
  classify "$svc"

  case "$CLS" in
    starting)
      DOWN_COUNT[$svc]=0
      return ;;
    ok)
      DOWN_COUNT[$svc]=0
      if [ "${ALERTED[$svc]:-0}" = 1 ]; then
        ALERTED[$svc]=0
        GAVE_UP[$svc]=0
        alert "$svc da hoat dong tro lai"
      fi
      return ;;
    down)
      DOWN_COUNT[$svc]=$(( ${DOWN_COUNT[$svc]:-0} + 1 ))
      # Cho DOWN_THRESHOLD vong: co the dang deploy, container dang duoc tao lai
      (( ${DOWN_COUNT[$svc]} < DOWN_THRESHOLD )) && return ;;
    *)
      DOWN_COUNT[$svc]=0 ;;
  esac

  if [ "$CLS" = unhealthy ] && [ "$kind" = app ] && [ "${GAVE_UP[$svc]:-0}" != 1 ]; then
    prune_restarts "$svc" "$now"
    if (( RECENT < MAX_RESTARTS )); then
      cid=$(container_id "$svc")
      if docker restart -t 10 "$cid" >/dev/null 2>&1; then
        RESTART_LOG[$svc]+="$now "
        ALERTED[$svc]=1
        alert "$svc unhealthy -> da tu restart ($(( RECENT + 1 ))/$MAX_RESTARTS trong $(( RESTART_WINDOW / 60 )) phut)"
      elif [ "${ALERTED[$svc]:-0}" != 1 ]; then
        ALERTED[$svc]=1
        alert "$svc unhealthy nhung 'docker restart' that bai - can kiem tra tay"
      fi
    else
      GAVE_UP[$svc]=1
      ALERTED[$svc]=1
      alert "$svc van unhealthy sau $MAX_RESTARTS lan restart - watcher bo cuoc, can kiem tra tay"
    fi
  elif [ "${ALERTED[$svc]:-0}" != 1 ]; then
    ALERTED[$svc]=1
    alert "$svc: $CLS ($DETAIL) - watcher chi bao, khong tu restart"
  fi
}

check_host() {
  local disk mem_mb
  disk=$(df --output=pcent / | tail -n 1 | tr -dc '0-9')
  if [ -n "$disk" ] && (( disk >= DISK_ALERT_PERCENT )); then
    cooldown_alert disk "O dia / da dung ${disk}% (nguong ${DISK_ALERT_PERCENT}%)"
  fi

  mem_mb=$(awk '/^MemAvailable:/ {print int($2/1024)}' /proc/meminfo)
  if [ -n "$mem_mb" ] && (( mem_mb < MEM_ALERT_MB )); then
    cooldown_alert mem "RAM kha dung chi con ${mem_mb}MB (nguong ${MEM_ALERT_MB}MB)"
  fi

  if ! systemctl is-active --quiet nginx; then
    cooldown_alert nginx "nginx khong chay - API cong khai khong truy cap duoc"
  fi
}

log "Watcher khoi dong: project=$PROJECT app=[$APP_SERVICES] data=[$DATA_SERVICES] poll=${POLL_INTERVAL}s"
alert "watcher da khoi dong"

while true; do
  if docker ps -q >/dev/null 2>&1; then
    for svc in $APP_SERVICES; do check_service "$svc" app; done
    for svc in $DATA_SERVICES; do check_service "$svc" data; done
  else
    cooldown_alert docker "Docker daemon khong phan hoi"
  fi
  check_host
  sleep "$POLL_INTERVAL"
done
