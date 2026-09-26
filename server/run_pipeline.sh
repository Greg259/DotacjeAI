#!/usr/bin/env bash
set -uo pipefail

APP_ROOT="${APP_ROOT:-/opt/dotacje-ai/app}"
crawl_status=0
extract_status=0
discovery_status=0

"${APP_ROOT}/server/run_crawler.sh" "$@" || crawl_status=$?
"${APP_ROOT}/server/run_discovery.sh" || discovery_status=$?
"${APP_ROOT}/server/run_extraction.sh" || extract_status=$?

if test "${crawl_status}" -ne 0 || test "${discovery_status}" -ne 0 || test "${extract_status}" -ne 0; then
  printf 'Pipeline zakończony z błędem: crawler=%s discovery=%s extractor=%s\n' "${crawl_status}" "${discovery_status}" "${extract_status}" >&2
  exit 1
fi
printf 'Pipeline crawler -> extraction zakończony poprawnie\n'
