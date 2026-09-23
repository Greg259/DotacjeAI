#!/usr/bin/env bash
set -Eeuo pipefail

umask 077
BACKUP_ROOT="${BACKUP_ROOT:-/opt/dotacje-ai/backups}"
SECRETS_ROOT="${SECRETS_ROOT:-/opt/dotacje-ai/secrets}"
RESTIC_ENV="${SECRETS_ROOT}/restic.env"
RESTORE_ROOT="$(mktemp -d "${BACKUP_ROOT}/restore-test.XXXXXX")"
cleanup() { rm -rf -- "${RESTORE_ROOT}"; }
trap cleanup EXIT

test -r "${RESTIC_ENV}" || { echo "Brak ${RESTIC_ENV}" >&2; exit 1; }
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
printf 'Test odczytu repozytorium, odtworzenia plików i sum kontrolnych zakończony poprawnie.\n'
