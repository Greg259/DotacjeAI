#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
DATA_ROOT="${DATA_ROOT:-/opt/dotacje-ai/data}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/dotacje-ai/backups}"
SECRETS_ROOT="${SECRETS_ROOT:-/opt/dotacje-ai/secrets}"
COMPOSE_FILE="${APP_ROOT}/infra/docker-compose.yml"
APP_ENV="${SECRETS_ROOT}/app.env"
RESTIC_ENV="${SECRETS_ROOT}/restic.env"
SUCCESS_MARKER="${BACKUP_ROOT}/last-successful-backup"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SNAPSHOT_DIR="${BACKUP_ROOT}/staging/${TIMESTAMP}"

log() { printf '%s %s\n' "$(date --iso-8601=seconds)" "$*"; }
fail() { log "ERROR: $*" >&2; exit 1; }

for command_name in docker restic flock sha256sum; do
  command -v "${command_name}" >/dev/null 2>&1 || fail "Brak polecenia: ${command_name}"
done
for required_file in "${COMPOSE_FILE}" "${APP_ENV}" "${RESTIC_ENV}"; do
  test -r "${required_file}" || fail "Brak pliku lub prawa odczytu: ${required_file}"
done

mkdir -p "${BACKUP_ROOT}/staging" "${BACKUP_ROOT}/logs"
exec 9>"${BACKUP_ROOT}/.backup.lock"
flock -n 9 || fail "Inny backup jest już uruchomiony"

set -a
# shellcheck disable=SC1090
source "${RESTIC_ENV}"
set +a

test -n "${RESTIC_REPOSITORY:-}" || fail "RESTIC_REPOSITORY nie jest ustawione"
test -n "${RESTIC_PASSWORD_FILE:-}" || fail "RESTIC_PASSWORD_FILE nie jest ustawione"
test -r "${RESTIC_PASSWORD_FILE}" || fail "Brak pliku hasła Restic"

mkdir -p "${SNAPSHOT_DIR}"
trap 'rm -rf -- "${SNAPSHOT_DIR}"' EXIT

log "Tworzenie pg_dump"
docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" exec -T postgres \
  sh -c 'exec pg_dump --format=custom --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  >"${SNAPSHOT_DIR}/postgres.dump.tmp"
mv "${SNAPSHOT_DIR}/postgres.dump.tmp" "${SNAPSHOT_DIR}/postgres.dump"

log "Walidacja formatu pg_dump"
docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" exec -T postgres \
  pg_restore --list <"${SNAPSHOT_DIR}/postgres.dump" >/dev/null

sha256sum "${SNAPSHOT_DIR}/postgres.dump" >"${SNAPSHOT_DIR}/SHA256SUMS"
printf 'created_utc=%s\nhost=%s\n' "${TIMESTAMP}" "$(hostname -f)" >"${SNAPSHOT_DIR}/metadata.txt"

backup_paths=("${SNAPSHOT_DIR}")
for data_dir in documents uploads exports; do
  mkdir -p "${DATA_ROOT}/${data_dir}"
  backup_paths+=("${DATA_ROOT}/${data_dir}")
done

log "Wysyłanie szyfrowanego snapshotu Restic"
restic backup "${backup_paths[@]}" --tag dotacje-ai --host "$(hostname -s)"

log "Stosowanie retencji: 7 dziennych, 5 tygodniowych, 12 miesięcznych"
restic forget --tag dotacje-ai --keep-daily 7 --keep-weekly 5 --keep-monthly 12 --prune

date -u --iso-8601=seconds >"${SUCCESS_MARKER}.tmp"
mv "${SUCCESS_MARKER}.tmp" "${SUCCESS_MARKER}"
log "Backup zakończony poprawnie"
