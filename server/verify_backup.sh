#!/usr/bin/env bash
set -Eeuo pipefail

umask 077
BACKUP_ROOT="${BACKUP_ROOT:-/opt/dotacje-ai/backups}"
SECRETS_ROOT="${SECRETS_ROOT:-/opt/dotacje-ai/secrets}"
APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
RESTIC_ENV="${SECRETS_ROOT}/restic.env"
APP_ENV="${SECRETS_ROOT}/app.env"
COMPOSE_FILE="${APP_ROOT}/infra/docker-compose.yml"
RESTORE_ROOT="$(mktemp -d "${BACKUP_ROOT}/restore-test.XXXXXX")"
TEST_DATABASE="dotacje_restore_test_$(date -u +%Y%m%d%H%M%S)"
DATABASE_CREATED=false

cleanup() {
  if test "${DATABASE_CREATED}" = true; then
    docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" exec -T postgres \
      sh -c 'dropdb --if-exists --username="$POSTGRES_USER" "$1"' sh "${TEST_DATABASE}" >/dev/null 2>&1 || true
  fi
  rm -rf -- "${RESTORE_ROOT}"
}
trap cleanup EXIT

test -r "${RESTIC_ENV}" || { echo "Brak ${RESTIC_ENV}" >&2; exit 1; }
test -r "${APP_ENV}" || { echo "Brak ${APP_ENV}" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "${RESTIC_ENV}"
set +a

restic check --read-data-subset=5%
restic restore latest --tag dotacje-ai --target "${RESTORE_ROOT}"
DUMP_FILE="$(find "${RESTORE_ROOT}" -type f -name postgres.dump -print -quit)"
test -n "${DUMP_FILE}" || { echo "Nie znaleziono postgres.dump" >&2; exit 1; }
test -s "${DUMP_FILE}" || { echo "postgres.dump jest pusty" >&2; exit 1; }
CHECKSUM_FILE="$(dirname "${DUMP_FILE}")/SHA256SUMS"
test -r "${CHECKSUM_FILE}" || { echo "Nie znaleziono SHA256SUMS" >&2; exit 1; }
(cd "$(dirname "${DUMP_FILE}")" && sha256sum --check SHA256SUMS)

docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" exec -T postgres \
  sh -c 'createdb --username="$POSTGRES_USER" "$1"' sh "${TEST_DATABASE}"
DATABASE_CREATED=true
docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" exec -T postgres \
  sh -c 'pg_restore --exit-on-error --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$1"' \
  sh "${TEST_DATABASE}" <"${DUMP_FILE}"
docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" exec -T postgres \
  sh -c 'psql --username="$POSTGRES_USER" --dbname="$1" --tuples-only --command="SELECT 1"' \
  sh "${TEST_DATABASE}" | grep -q '1'

printf 'Test Restic, sum kontrolnych i pełnego importu do tymczasowej bazy zakończony poprawnie.\n'
