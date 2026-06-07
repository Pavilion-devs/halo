# TrueFoundry Registration Checklist

## Backend Deployment

1. Deploy `apps/api` with Python 3.12.
2. Use `apps/api/Dockerfile` or the start command in `infra/deploy/backend-deployment.md`.
3. Set environment from `infra/deploy/backend.env.example`.
4. Confirm:
   - `GET /health`
   - `GET /readiness`
   - `GET /incidents`
   - `GET /openapi/incident-api.yaml`
   - `GET /openapi/runbooks-api.yaml`
5. Ensure the public API origin is reachable from TrueFoundry.

## MCP Registration

1. Register OpenAPI MCP server `incident-api`.
2. Use OpenAPI spec `infra/openapi/incident-api.yaml`.
3. Use spec URL `<HALO_PUBLIC_API_BASE_URL>/openapi/incident-api.yaml` or paste the spec content.
4. Set OpenAPI server URL to the deployed Halo API origin.
5. Register OpenAPI MCP server `runbooks-api`.
6. Use spec URL `<HALO_PUBLIC_API_BASE_URL>/openapi/runbooks-api.yaml` or paste the spec content.
7. Set OpenAPI server URL to the deployed Halo API origin.
8. Validate generated tools:
   - `getHealthSummary`
   - `getRecentDeploys`
   - `getTopErrors`
   - `getIncidentContext`
   - `getRecentStatusEvents`
   - `searchRunbooks`
   - `getRunbook`

## Virtual MCP Servers

1. Create `halo-observe`.
2. Add only read tools from `incident-api` and `runbooks-api`.
3. Exclude demo chaos tools from `halo-observe`.
4. Create `halo-act`.
5. Add only approved Slack/GitHub write tools once those servers exist.
6. Do not add destructive, rollback, delete, shell, or broad update tools.

## Saved Agents

1. Create or update `halo-normal`.
2. Attach model `halo-vm-normal`.
3. Attach virtual MCP servers `halo-observe` and `halo-act`.
4. Set iteration limit `5`.
5. Create or update `halo-degraded`.
6. Attach model `halo-vm-degraded`.
7. Attach `halo-observe` only.
8. Set iteration limit `3`.
9. Create or update `halo-blackout`.
10. Attach model `halo-vm-degraded` or `bedrock-nova-micro-fast`.
11. Attach `halo-observe` only or no tools if observe is unstable.
12. Set iteration limit `2`.

## Trace Validation

1. Set:
   - `HALO_TRUEFOUNDRY_TRACES_ENABLED=true`
   - `HALO_TRUEFOUNDRY_TRACES_QUERY_PATH=/api/svc/v1/spans/query`
   - `HALO_TRUEFOUNDRY_TRACES_DATA_ROUTING_DESTINATION=default`
2. Create and run an incident with `scenario=registration-smoke`.
3. Call `GET /incidents/{incident_id}/traces`.
4. Confirm `lookup_status=found` after TrueFoundry spans become available.
