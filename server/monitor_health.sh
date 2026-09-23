#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/dotacje-ai/backups}"
SECRETS_ROOT="${SECRETS_ROOT:-/opt/dotacje-ai/secrets}"
APP_ENV="${SECRETS_ROOT}/app.env"
MONITOR_ENV="${SECRETS_ROOT}/monitoring.env"
COMPOSE_FILE="${APP_ROOT}/infra/docker-compose.yml"
MAX_DISK_PERCENT="${MAX_DISK_PERCENT:-80}"
MAX_BACKUP_AGE_HOURS="${MAX_BACKUP_AGE_HOURS:-36}"
errors=()

if test -r "${MONITOR_ENV}"; then
  set -a
  # shellcheck disable=SC1090
  source "${MONITOR_ENV}"
  set +a
fi

check_url() {
  local url="$1"
  curl --fail --silent --show-error --max-time 15 --retry 2 "${url}" >/dev/null || errors+=("HTTP nie odpowiada: ${url}")
}

check_url "https://dotacjeai.eu/health"
check_url "https://dotacjeai.eu/api/health"

for service in caddy frontend api postgres redis; do
  container_id="$(docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" ps -q "${service}" 2>/dev/null || true)"
  if test -z "${container_id}"; then
    errors+=("Brak kontenera: ${service}")
    continue
  fi
  state="$(docker inspect --format '{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "${container_id}" 2>/dev/null || true)"
  test "${state}" = "running/healthy" || errors+=("Kontener ${service}: ${state:-unknown}")
done

disk_percent="$(df -P /opt/dotacje-ai | awk 'NR==2 {gsub(/%/, "", $5); print $5}')"
if test -z "${disk_percent}" || test "${disk_percent}" -ge "${MAX_DISK_PERCENT}"; then
  errors+=("Użycie dysku: ${disk_percent:-unknown}% (próg ${MAX_DISK_PERCENT}%)")
fi

success_marker="${BACKUP_ROOT}/last-successful-backup"
if test ! -r "${success_marker}"; then
  errors+=("Brak znacznika poprawnego backupu")
else
  marker_epoch="$(date -d "$(cat "${success_marker}")" +%s 2>/dev/null || echo 0)"
  now_epoch="$(date +%s)"
  backup_age_hours="$(( (now_epoch - marker_epoch) / 3600 ))"
  test "${backup_age_hours}" -le "${MAX_BACKUP_AGE_HOURS}" || errors+=("Ostatni backup ma ${backup_age_hours} h (próg ${MAX_BACKUP_AGE_HOURS} h)")
fi

if test "${#errors[@]}" -gt 0; then
  printf '%s ERROR %s\n' "$(date --iso-8601=seconds)" "${errors[*]}" >&2
  exit 1
fi
if test -n "${MONITOR_HEARTBEAT_URL:-}"; then
  curl --fail --silent --show-error --max-time 15 --retry 2 "${MONITOR_HEARTBEAT_URL}" >/dev/null
fi
printf '%s OK HTTPS, API, kontenery, dysk i świeżość backupu\n' "$(date --iso-8601=seconds)"
