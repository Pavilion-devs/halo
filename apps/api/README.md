# Halo API

FastAPI service for the Halo incident workflow scaffold.

## Local Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

OpenAPI docs are available at `http://localhost:8000/docs`.

## Current Scope

- SQLite-backed incident store through SQLModel
- Typed Pydantic schemas
- Incident routes for create, list, detail, run, and approve
- Workflow placeholder that advances deterministic stages and records events/checkpoints
- Deterministic `incident-api` and `runbooks-api` surfaces for future OpenAPI-to-MCP use
- Optional TrueFoundry agent and trace wrappers, disabled by default for local development

## Persistence

The default database URL is `sqlite:///./halo.db`. Override it with:

```bash
HALO_DATABASE_URL=sqlite:///./local-halo.db uvicorn app.main:app --reload
```

The repository stores the full incident aggregate:

- incidents
- incident events
- incident checkpoints
- approvals
- trace links

## Custom API Surfaces

The service also exposes deterministic demo-safe endpoints matching the OpenAPI specs:

- `GET /health/summary`
- `GET /deploys/recent`
- `GET /errors/top`
- `GET /incidents/{incident_id}/context`
- `GET /status/events/recent`
- `GET /runbooks/search`
- `GET /runbooks/{slug}`
- `POST /demo/fail-next`
- `POST /demo/delay-next`
- `POST /demo/return-bad-payload`

Chaos controls accept optional `incident_id` and `scenario` query parameters. A chaos
rule is consumed only by a request with matching target context. If no target is supplied
when arming a rule, it is assigned to `scenario=default-demo` and will not affect
untargeted background requests.

Trace links persist with a stable internal `id`, external `trace_id`, metadata, and
`created_at`; repository reloads return them in chronological order.

## TrueFoundry Agent Invocation

TrueFoundry integration is disabled by default. Configure it with:

```bash
HALO_TRUEFOUNDRY_ENABLED=true
HALO_TRUEFOUNDRY_BASE_URL=https://<truefoundry-gateway-host>
HALO_TRUEFOUNDRY_VIRTUAL_ACCOUNT_TOKEN=<token>
HALO_TRUEFOUNDRY_AGENT_NAME_NORMAL=halo-normal
HALO_TRUEFOUNDRY_AGENT_NAME_DEGRADED=halo-degraded
HALO_TRUEFOUNDRY_AGENT_NAME_BLACKOUT=halo-blackout
HALO_TRUEFOUNDRY_AGENT_ID_NORMAL=
HALO_TRUEFOUNDRY_AGENT_ID_DEGRADED=
HALO_TRUEFOUNDRY_AGENT_ID_BLACKOUT=
HALO_TRUEFOUNDRY_MODEL_NORMAL=halo/halo-vm-normal
HALO_TRUEFOUNDRY_MODEL_DEGRADED=halo/halo-vm-degraded
HALO_TRUEFOUNDRY_MODEL_BLACKOUT=halo/halo-vm-degraded
HALO_TRUEFOUNDRY_REQUEST_TIMEOUT_SECONDS=20
HALO_TRUEFOUNDRY_USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
HALO_TRUEFOUNDRY_AGENT_VERSIONS_PATH=/api/svc/v1/agent-versions
```

When enabled and configured, `POST /incidents/{id}/run` invokes:

- `GET /api/svc/v1/agent-versions` to resolve saved-agent app IDs by `manifest.name`,
  unless explicit `HALO_TRUEFOUNDRY_AGENT_ID_*` values are configured
- `POST /api/llm/agent/{agent_app_id}/responses`
- `model` is sent because the live workspace requires it when no load-balance rule is
  configured
- `Authorization: Bearer <token>`
- `X-TFY-METADATA` with incident, mode, scenario, demo, product, and stage fields

If disabled or missing configuration, the deterministic local workflow runs without
network calls.

## TrueFoundry Trace Lookup

Trace lookup is also disabled by default. Configure it with:

```bash
HALO_TRUEFOUNDRY_TRACES_ENABLED=true
HALO_TRUEFOUNDRY_TRACES_BASE_URL=https://<truefoundry-trace-host>
HALO_TRUEFOUNDRY_TRACES_TIMEOUT_SECONDS=10
HALO_TRUEFOUNDRY_TRACES_QUERY_PATH=/api/svc/v1/spans/query
HALO_TRUEFOUNDRY_TRACES_DATA_ROUTING_DESTINATION=default
HALO_TRUEFOUNDRY_TRACES_LOOKBACK_HOURS=24
```

If `HALO_TRUEFOUNDRY_TRACES_BASE_URL` is not set, Halo falls back to
`HALO_TRUEFOUNDRY_BASE_URL`. Trace lookup uses TrueFoundry's spans query API.

Trace data is exposed at:

- `GET /incidents/{incident_id}/traces`

When trace lookup is disabled or unconfigured, this endpoint returns persisted trace
links only. When enabled, it attempts live enrichment per trace and returns partial
data with an `error` field if lookup fails.
