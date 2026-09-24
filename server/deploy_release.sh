#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_COMMIT="${1:?Podaj pelny SHA commitu do wdrozenia}"
APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
SECRETS_FILE="${SECRETS_FILE:-/opt/dotacje-ai/secrets/app.env}"
ADMIN_PASSWORD_FILE="${ADMIN_PASSWORD_FILE:-/opt/dotacje-ai/secrets/admin-initial-password}"
REPOSITORY_URL="${REPOSITORY_URL:-https://github.com/Greg259/DotacjeAI.git}"
RELEASE_TMP="$(mktemp -d)"
trap 'rm -rf -- "${RELEASE_TMP}"' EXIT

if test "${APP_ROOT}" != "/opt/dotacje-ai/app"; then
  printf 'Odmowa: nieoczekiwany APP_ROOT: %s\n' "${APP_ROOT}" >&2
  exit 1
fi
test -d "${APP_ROOT}"
test -f "${SECRETS_FILE}"

"${APP_ROOT}/server/backup_dotacje_ai.sh"

git clone --quiet --no-tags "${REPOSITORY_URL}" "${RELEASE_TMP}/repo"
ACTUAL_COMMIT="$(git -C "${RELEASE_TMP}/repo" rev-parse HEAD)"
if test "${ACTUAL_COMMIT}" != "${EXPECTED_COMMIT}"; then
  printf 'Odmowa: oczekiwano %s, pobrano %s\n' "${EXPECTED_COMMIT}" "${ACTUAL_COMMIT}" >&2
  exit 1
fi

if ! grep -q '^ADMIN_PASSWORD_HASH=' "${SECRETS_FILE}" || grep -q 'CHANGE_ME_WITH_CADDY_HASH_PASSWORD' "${SECRETS_FILE}"; then
  umask 077
  ADMIN_PASSWORD="$(openssl rand -hex 20)"
  printf '%s\n' "${ADMIN_PASSWORD}" >"${ADMIN_PASSWORD_FILE}"
  ADMIN_HASH="$(docker run --rm caddy:2-alpine caddy hash-password --plaintext "${ADMIN_PASSWORD}")"
  ENV_TMP="$(mktemp)"
  grep -v '^ADMIN_USERNAME=' "${SECRETS_FILE}" | grep -v '^ADMIN_PASSWORD_HASH=' >"${ENV_TMP}"
  printf '%s\n' 'ADMIN_USERNAME=admin' "ADMIN_PASSWORD_HASH='${ADMIN_HASH}'" >>"${ENV_TMP}"
  chmod 0600 "${ENV_TMP}"
  mv "${ENV_TMP}" "${SECRETS_FILE}"
fi

rsync -a --delete --exclude='.git/' "${RELEASE_TMP}/repo/" "${APP_ROOT}/"

docker compose --env-file "${SECRETS_FILE}" --file "${APP_ROOT}/infra/docker-compose.yml" config --quiet
docker compose --env-file "${SECRETS_FILE}" --file "${APP_ROOT}/infra/docker-compose.yml" up -d --build
docker compose --env-file "${SECRETS_FILE}" --file "${APP_ROOT}/infra/docker-compose.yml" restart caddy
docker compose --env-file "${SECRETS_FILE}" --file "${APP_ROOT}/infra/docker-compose.yml" run --rm --no-deps -T review python -m app.cli.seed_sources
"${APP_ROOT}/server/install_user_cron.sh"

printf 'Wdrożono commit %s\n' "${ACTUAL_COMMIT}"
