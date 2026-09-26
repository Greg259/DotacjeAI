#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
SECRETS_ROOT="${SECRETS_ROOT:-/opt/dotacje-ai/secrets}"
APP_ENV="${SECRETS_ROOT}/app.env"
COMPOSE_FILE="${APP_ROOT}/infra/docker-compose.yml"
ADMIN_PASSWORD_FILE="${SECRETS_ROOT}/admin-initial-password"
ADMIN_HTML="$(mktemp)"
trap 'rm -f -- "${ADMIN_HTML}"' EXIT

test -r "${APP_ENV}"
test -r "${ADMIN_PASSWORD_FILE}"
test -r "${APP_ROOT}/.deployed-commit"

printf 'commit=%s\n' "$(cat "${APP_ROOT}/.deployed-commit")"
docker compose --env-file "${APP_ENV}" -f "${COMPOSE_FILE}" ps

test "$(curl --fail --silent --show-error https://dotacjeai.eu/health)" = "ok"
echo 'OK /health'
curl --fail --silent --show-error https://dotacjeai.eu/api/health | grep -q '"status":"ok"'
echo 'OK /api/health'
curl --fail --silent --show-error 'https://dotacjeai.eu/api/programs?limit=10' | grep -q '"total":3'
echo 'OK 3 publiczne programy'
curl --fail --silent --show-error https://dotacjeai.eu/sitemap.xml | grep -q '<loc>https://dotacjeai.eu/dotacje/'
echo 'OK sitemap'

unauthorized_status="$(curl --silent --output /dev/null --write-out '%{http_code}' https://dotacjeai.eu/admin)"
test "${unauthorized_status}" = "401"
admin_password="$(cat "${ADMIN_PASSWORD_FILE}")"
authorized_status="$(curl --silent --user "admin:${admin_password}" --output "${ADMIN_HTML}" --write-out '%{http_code}' https://dotacjeai.eu/admin)"
test "${authorized_status}" = "200"
printf 'OK panel admin %s/%s\n' "${unauthorized_status}" "${authorized_status}"
grep -q '<strong>3</strong><br>programów publicznych' "${ADMIN_HTML}"
grep -q '<strong>0</strong><br>zadań REVIEW' "${ADMIN_HTML}"
grep -q '<strong>0</strong><br>niedostępnych dokumentów' "${ADMIN_HTML}"
echo 'OK metryki panelu: 3 programy, 0 REVIEW, 0 niedostępnych dokumentów'

headers="$(curl --fail --silent --show-error --head https://dotacjeai.eu/)"
grep -qi '^strict-transport-security:' <<<"${headers}"
grep -qi '^content-security-policy:' <<<"${headers}"
grep -qi '^x-frame-options:' <<<"${headers}"
grep -qi '^permissions-policy:' <<<"${headers}"
grep -qi '^x-content-type-options:' <<<"${headers}"
if grep -qi '^x-powered-by:' <<<"${headers}"; then
  echo 'Niepożądany nagłówek X-Powered-By jest obecny.' >&2
  exit 1
fi

printf 'OK commit, kontenery, health, 3 programy, sitemap, panel 401/200, 0 REVIEW, 0 niedostępnych dokumentów i nagłówki bezpieczeństwa.\n'
