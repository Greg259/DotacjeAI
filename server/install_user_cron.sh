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
  "15 */6 * * * ${APP_ROOT}/server/run_pipeline.sh >> ${BACKUP_ROOT}/logs/pipeline.log 2>&1 # dotacje-ai-pipeline" \
  "10 4 * * * ${APP_ROOT}/server/run_document_sync.sh >> ${BACKUP_ROOT}/logs/documents.log 2>&1 # dotacje-ai-documents" \
  "25 * * * * ${APP_ROOT}/server/run_status_refresh.sh >> ${BACKUP_ROOT}/logs/status.log 2>&1 # dotacje-ai-status" \
  >>"${CRON_TMP}"

crontab "${CRON_TMP}"
printf 'Zainstalowano harmonogram użytkownika %s:\n' "$(id -un)"
crontab -l | grep '# dotacje-ai-'
