# Public API Readiness

TrueFoundry must be able to reach the Halo API origin used in MCP registration.

## Required Public Paths

- `GET /health`
- `GET /readiness`
- `GET /health/summary`
- `GET /deploys/recent`
- `GET /errors/top`
- `GET /incidents/{incident_id}/context`
- `GET /status/events/recent`
- `GET /runbooks/search?q=checkout`
- `GET /runbooks/checkout-api-5xx`
- `GET /openapi/incident-api.yaml`
- `GET /openapi/runbooks-api.yaml`

## Optional Demo Chaos Paths

Do not attach these tools to production saved agents:

- `POST /demo/fail-next`
- `POST /demo/delay-next`
- `POST /demo/return-bad-payload`

## Required Secrets

- TrueFoundry Virtual Account Token for Halo backend.
- Optional Halo custom API token if the public API is protected.
- Any GitHub/Slack credentials needed later for native/remote MCP servers.

## Validation Commands

```bash
export HALO_PUBLIC_API_BASE_URL=https://PLACEHOLDER_PUBLIC_HALO_API_BASE_URL

curl -fsS "$HALO_PUBLIC_API_BASE_URL/health"
curl -fsS "$HALO_PUBLIC_API_BASE_URL/readiness"
curl -fsS "$HALO_PUBLIC_API_BASE_URL/health/summary"
curl -fsS "$HALO_PUBLIC_API_BASE_URL/runbooks/search?q=checkout"
curl -fsS "$HALO_PUBLIC_API_BASE_URL/runbooks/checkout-api-5xx"
curl -fsS "$HALO_PUBLIC_API_BASE_URL/openapi/incident-api.yaml"
curl -fsS "$HALO_PUBLIC_API_BASE_URL/openapi/runbooks-api.yaml"
```

All commands should return JSON without requiring browser cookies.
