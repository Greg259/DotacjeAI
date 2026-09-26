#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
SECRETS_FILE="${SECRETS_FILE:-/opt/dotacje-ai/secrets/app.env}"

docker compose \
  --env-file "${SECRETS_FILE}" \
  --file "${APP_ROOT}/infra/docker-compose.yml" \
  run --rm --no-deps crawler python -m app.cli.discover_programs
