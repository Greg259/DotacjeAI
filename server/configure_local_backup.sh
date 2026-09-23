#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

BACKUP_ROOT="${BACKUP_ROOT:-/opt/dotacje-ai/backups}"
SECRETS_ROOT="${SECRETS_ROOT:-/opt/dotacje-ai/secrets}"
RESTIC_REPOSITORY="${BACKUP_ROOT}/restic-repository"
RESTIC_PASSWORD_FILE="${SECRETS_ROOT}/restic-password"
RESTIC_ENV="${SECRETS_ROOT}/restic.env"

command -v restic >/dev/null 2>&1 || { echo "Brak programu restic" >&2; exit 1; }
command -v openssl >/dev/null 2>&1 || { echo "Brak programu openssl" >&2; exit 1; }

mkdir -p "${BACKUP_ROOT}/logs" "${BACKUP_ROOT}/staging" "${SECRETS_ROOT}"
chmod 700 "${BACKUP_ROOT}" "${SECRETS_ROOT}"

if test ! -s "${RESTIC_PASSWORD_FILE}"; then
  password_tmp="${RESTIC_PASSWORD_FILE}.tmp"
  openssl rand -base64 48 >"${password_tmp}"
  chmod 600 "${password_tmp}"
  mv "${password_tmp}" "${RESTIC_PASSWORD_FILE}"
fi

env_tmp="${RESTIC_ENV}.tmp"
printf 'RESTIC_REPOSITORY=%s\nRESTIC_PASSWORD_FILE=%s\n' \
  "${RESTIC_REPOSITORY}" "${RESTIC_PASSWORD_FILE}" >"${env_tmp}"
chmod 600 "${env_tmp}"
mv "${env_tmp}" "${RESTIC_ENV}"

export RESTIC_REPOSITORY RESTIC_PASSWORD_FILE
if test ! -f "${RESTIC_REPOSITORY}/config"; then
  restic init
else
  restic snapshots >/dev/null
fi

printf 'Lokalne repozytorium Restic jest gotowe: %s\n' "${RESTIC_REPOSITORY}"
printf 'Hasło pozostaje wyłącznie w chronionym pliku: %s\n' "${RESTIC_PASSWORD_FILE}"
