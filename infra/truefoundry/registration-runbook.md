# TrueFoundry Registration Runbook

This runbook prepares MCP and saved-agent registration. It does not assume credentials
are present locally.

## Preconditions

- TrueFoundry SaaS workspace access is available.
- `aws-bedrock-halo` provider account exists.
- Virtual models exist:
  - `halo-vm-normal`
  - `halo-vm-degraded`
  - `halo-vm-chaos-demo`
- Halo API is reachable from TrueFoundry at `PLACEHOLDER_PUBLIC_HALO_API_BASE_URL`.
- Any API auth token is stored as a TrueFoundry secret.

## Register OpenAPI MCP Servers

1. Register `incident-api` from `infra/openapi/incident-api.yaml`.
2. Register `runbooks-api` from `infra/openapi/runbooks-api.yaml`.
3. Set both server base URLs to the deployed Halo API origin.
4. Attach read-only service auth if the API is not public.
5. Validate one read operation from each:
   - `getHealthSummary`
   - `searchRunbooks`

Fields in `mcp-servers.yaml` marked `PLACEHOLDER_REQUIRE_TFY_CONFIRMATION` must be
mapped to the exact TrueFoundry API/UI names during live registration.

## Create Virtual MCP Servers

1. Create `halo-observe`.
2. Include only read operations from:
   - `incident-api`
   - `runbooks-api`
   - future GitHub read tools
   - future Slack read tools
3. Create `halo-act`.
4. Include only low-risk approved write operations:
   - post incident update
   - create issue/ticket
5. Do not include demo chaos operations in either production virtual server.

## Create Saved Agents

Use `infra/truefoundry/agents.yaml` as the attachment matrix:

- `halo-normal`: `halo-vm-normal`, `halo-observe`, `halo-act`, limit `5`
- `halo-degraded`: `halo-vm-degraded`, `halo-observe`, limit `3`
- `halo-blackout`: `halo-vm-degraded`, `halo-observe`, limit `2`

Attach `halo-guardrails` to all three agents once guardrail policy names are confirmed.

## Backend Configuration

Set:

```bash
HALO_TRUEFOUNDRY_ENABLED=true
HALO_TRUEFOUNDRY_BASE_URL=<agent gateway base url>
HALO_TRUEFOUNDRY_VIRTUAL_ACCOUNT_TOKEN=<virtual account token>
HALO_TRUEFOUNDRY_TRACES_ENABLED=true
HALO_TRUEFOUNDRY_TRACES_BASE_URL=<trace/log query base url if different>
HALO_TRUEFOUNDRY_TRACES_QUERY_PATH=/api/svc/v1/spans/query
HALO_TRUEFOUNDRY_TRACES_DATA_ROUTING_DESTINATION=default
HALO_TRUEFOUNDRY_TRACES_LOOKBACK_HOURS=24
```

Trace lookup uses the documented spans query endpoint:

- `POST /api/svc/v1/spans/query`
- body includes `startTime`, `endTime`, `traceIds`, `dataRoutingDestination`, `limit`,
  and `sortDirection`

## Validation

1. Create an incident in Halo.
2. Run one workflow step with `scenario=registration-smoke`.
3. Confirm `X-TFY-METADATA` appears in TrueFoundry request logs.
4. Confirm a trace/request ID is persisted in `trace_links`.
5. Call `GET /incidents/{id}/traces`.
6. Confirm persisted links are returned even if live trace lookup is unavailable.
7. Enable trace lookup and confirm `lookup_status=found` once spans are available.
