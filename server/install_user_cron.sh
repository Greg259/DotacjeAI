#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/dotacje-ai/backups}"
CRON_TMP="$(mktemp)"
trap 'rm -f -- "${CRON_TMP}"' EXIT

mkdir -p "${BACKUP_ROOT}/logs"

crontab -l 2>/dev/null \
  | grep -v '# dotacje-ai-' \
  >"${CRON_TMP}" || true

printf '%s\n' \
  "30 2 * * * ${APP_ROOT}/server/backup_dotacje_ai.sh >> ${BACKUP_ROOT}/logs/backup.log 2>&1 # dotacje-ai-backup" \
  "*/5 * * * * ${APP_ROOT}/server/monitor_health.sh >> ${BACKUP_ROOT}/logs/monitor.log 2>&1 # dotacje-ai-monitor" \
  "15 */6 * * * ${APP_ROOT}/server/run_crawler.sh >> ${BACKUP_ROOT}/logs/crawler.log 2>&1 # dotacje-ai-crawler" \
  >>"${CRON_TMP}"

crontab "${CRON_TMP}"
printf 'Zainstalowano harmonogram użytkownika %s:\n' "$(id -un)"
crontab -l | grep '# dotacje-ai-'
