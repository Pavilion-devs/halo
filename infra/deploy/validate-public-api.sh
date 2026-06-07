#!/usr/bin/env bash
set -euo pipefail

base_url="${HALO_PUBLIC_API_BASE_URL:-}"

if [[ -z "$base_url" ]]; then
  echo "Set HALO_PUBLIC_API_BASE_URL before running validation." >&2
  exit 1
fi

curl -fsS "$base_url/health" >/dev/null
curl -fsS "$base_url/readiness" >/dev/null
curl -fsS "$base_url/health/summary" >/dev/null
curl -fsS "$base_url/deploys/recent" >/dev/null
curl -fsS "$base_url/errors/top" >/dev/null
curl -fsS "$base_url/status/events/recent" >/dev/null
curl -fsS "$base_url/runbooks/search?q=checkout" >/dev/null
curl -fsS "$base_url/runbooks/checkout-api-5xx" >/dev/null
curl -fsS "$base_url/openapi/incident-api.yaml" >/dev/null
curl -fsS "$base_url/openapi/runbooks-api.yaml" >/dev/null

echo "Halo public API readiness checks passed."
