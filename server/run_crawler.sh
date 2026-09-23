#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
SECRETS_FILE="${SECRETS_FILE:-/opt/dotacje-ai/secrets/app.env}"
SNAPSHOT_ROOT="${SNAPSHOT_ROOT:-/opt/dotacje-ai/data/documents/sources}"

umask 027
mkdir -p "${SNAPSHOT_ROOT}"

docker compose \
  --env-file "${SECRETS_FILE}" \
  --file "${APP_ROOT}/infra/docker-compose.yml" \
  run --rm --no-deps crawler "$@"
