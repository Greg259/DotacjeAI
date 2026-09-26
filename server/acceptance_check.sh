#!/usr/bin/env bash
set -Eeuo pipefail

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
SECRETS_ROOT="${SECRETS_ROOT:-/opt/dotacje-ai/secrets}"
APP_ENV="${SECRETS_ROOT}/app.env"
COMPOSE_FILE="${APP_ROOT}/infra/docker-compose.yml"
EXPECTED_PROGRAM_COUNT="${EXPECTED_PROGRAM_COUNT:-11}"
EXPECTED_REVIEW_COUNT="${EXPECTED_REVIEW_COUNT:-0}"
EXPECTED_UNAVAILABLE_COUNT="${EXPECTED_UNAVAILABLE_COUNT:-1}"
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
curl --fail --silent --show-error 'https://dotacjeai.eu/api/programs?limit=20' | grep -q "\"total\":${EXPECTED_PROGRAM_COUNT}"
printf 'OK %s publicznych programów\n' "${EXPECTED_PROGRAM_COUNT}"
curl --fail --silent --show-error https://dotacjeai.eu/sitemap.xml | grep -q '<loc>https://dotacjeai.eu/dotacje/'
echo 'OK sitemap'
for public_path in /konto/logowanie /konto/rejestracja /regulamin /prywatnosc; do
  curl --fail --silent --show-error "https://dotacjeai.eu${public_path}" >/dev/null
done
echo 'OK strony konta i prywatności'
unauthenticated_account_status="$(curl --silent --output /dev/null --write-out '%{http_code}' https://dotacjeai.eu/api/auth/me)"
test "${unauthenticated_account_status}" = "401"
echo 'OK ochrona danych konta 401'

unauthorized_status="$(curl --silent --output /dev/null --write-out '%{http_code}' https://dotacjeai.eu/admin)"
test "${unauthorized_status}" = "401"
admin_password="$(cat "${ADMIN_PASSWORD_FILE}")"
authorized_status="$(curl --silent --user "admin:${admin_password}" --output "${ADMIN_HTML}" --write-out '%{http_code}' https://dotacjeai.eu/admin)"
test "${authorized_status}" = "200"
printf 'OK panel admin %s/%s\n' "${unauthorized_status}" "${authorized_status}"
grep -oE '<strong>[^<]+</strong><br>[^<]+</div>' "${ADMIN_HTML}" || true
grep -q "<strong>${EXPECTED_PROGRAM_COUNT}</strong><br>program" "${ADMIN_HTML}"
grep -q "<strong>${EXPECTED_REVIEW_COUNT}</strong><br>zadań REVIEW" "${ADMIN_HTML}"
grep -q "<strong>${EXPECTED_UNAVAILABLE_COUNT}</strong><br>niedostępnych dokumentów" "${ADMIN_HTML}"
printf 'OK metryki panelu: %s programów, %s REVIEW, %s niedostępnych dokumentów\n' \
  "${EXPECTED_PROGRAM_COUNT}" "${EXPECTED_REVIEW_COUNT}" "${EXPECTED_UNAVAILABLE_COUNT}"

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

printf 'OK commit, kontenery, health, %s programów, sitemap, panel 401/200, %s REVIEW, %s niedostępnych dokumentów i nagłówki bezpieczeństwa.\n' \
  "${EXPECTED_PROGRAM_COUNT}" "${EXPECTED_REVIEW_COUNT}" "${EXPECTED_UNAVAILABLE_COUNT}"
