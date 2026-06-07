# Halo Live Setup Status

Updated: 2026-06-06

## Deployment URL

- Temporary public URL validated: `https://8f42-102-216-203-245.ngrok-free.app`
- Deployment type: local `uvicorn` process exposed through `ngrok`
- Durability: temporary only; not a permanent deployment
- Permanent deployment URL: blocked, not available from this environment

## What Was Actually Deployed

- Halo API was restarted locally with:
  - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- `apps/api/.env` is loaded by the backend and contains live TrueFoundry settings.
- A public tunnel was started with:
  - `ngrok http 8000 --log=stdout`
- Public readiness validation passed through the tunnel:
  - `GET /health`
  - `GET /readiness`
  - `GET /health/summary`
  - `GET /deploys/recent`
  - `GET /errors/top`
  - `GET /status/events/recent`
  - `GET /runbooks/search?q=checkout`
  - `GET /runbooks/checkout-api-5xx`
  - `GET /openapi/incident-api.yaml`
  - `GET /openapi/runbooks-api.yaml`

## Smoke Test Results

### 2026-06-02 Bedrock Routing And MCP Tool Smoke

- Backend restart: succeeded after backend prompt/input changes.
- Backend PID after restart: `9258`
- Local/public health validation: passed.
- Backend changes:
  - Added a system instruction requiring at least two relevant `halo-observe` tool
    calls when evidence is incomplete.
  - Agent Responses body now includes:
    - `mcp_servers: [{"name": "halo-observe", "enable_all_tools": true}]`
  - Increased local `HALO_TRUEFOUNDRY_REQUEST_TIMEOUT_SECONDS` from `20` to `90`
    because tool-enabled agent loops exceeded the old timeout.

Normal routing verification:

- Incident: `inc_92668bb8959d`
- Invocation: succeeded.
- Trace lookup: `found`.
- Requested virtual model: `halo/halo-vm-normal`.
- Resolved live span model: `aws-bedrock/us.anthropic.claude-opus-4-6-v1`.
- Result: Bedrock-backed, but still not the desired Sonnet target.
- Desired `halo-vm-normal` routing remains:
  - priority `0`: `aws-bedrock/us.anthropic.claude-sonnet-4-6`
  - priority `1`: `aws-bedrock/qwen.qwen3-32b-v1-0`

Degraded routing verification:

- Incident: `inc_2f4be1148999`
- Invocation: succeeded.
- Trace lookup: `found`.
- Requested virtual model: `halo/halo-vm-degraded`.
- Resolved live span model: `aws-bedrock/us.anthropic.claude-haiku-4-5-20251001-v1-0`.
- Result: Bedrock-backed and matches the desired Haiku primary.

MCP/tool usage verification:

- Incident: `inc_571e8e5cfadc`
- Invocation: succeeded.
- Trace lookup: `found`.
- `mcp_tool_spans`: non-empty.
- Observed tool/server span examples:
  - `MCP: tools/call: getRecentDeploys (incident-api)`
  - `MCP: tools/call: getTopErrors (incident-api)`
  - `MCP: tools/call: getHealthSummary (incident-api)`
  - `MCP: tools/call: searchRunbooks (runbooks-api)`
  - `MCP: tools/call: getRecentDeploys_incid6c (halo-observe)`
  - `MCP: tools/call: getTopErrors_incid6c (halo-observe)`
  - `MCP: tools/call: getHealthSummary_incid6c (halo-observe)`
  - `MCP: tools/call: searchRunbooks_runbo53 (halo-observe)`
- The run showed some `MCP: incident-api` and `MCP: runbooks-api` parent spans with
  `Error` status, while the concrete tool-call spans returned `Ok`.

Guardrail prep status:

- Guardrail-visible trace is still blocked by missing live guardrail attachment.
- The next useful guardrail run should attach a simple visible MCP pre-invoke or
  post-invoke guardrail to `halo-observe` / `incident-api` tool calls, then rerun
  `inc_571e8e5cfadc`-style smoke and check `guardrails_triggered`.

### 2026-06-02 Successful Trace Correlation

- Backend restart: succeeded
- Fresh server process command:
  - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Backend PID after restart: `86448`
- Local route validation: passed
  - `GET /health`
  - `GET /readiness`
- Public ngrok validation: passed
- Backend trace-correlation changes:
  - Agent Responses requests now send `X-TFY-LOGGING-CONFIG: {"enabled":true}`
  - response headers captured when present:
    - `x-tfy-feedback-target-id`
    - `x-tfy-trace-id`
    - `x-request-id`
    - `x-tfy-request-id`
  - `x-tfy-feedback-target-id` is decoded when possible
  - decoded `traceId` is persisted as the primary trace link
  - decoded `spanId` and raw feedback target are persisted in trace metadata
  - `HALO_TRUEFOUNDRY_TRACES_TIMEOUT_SECONDS` was increased locally from `10` to `30`
- Created incident through public URL: `inc_d21e416dc1dd`
- Ran one workflow step through public URL:
  - resulting stage: `classify`
  - resulting mode: `normal`
  - current agent: `halo-normal`
  - latest recommendation: updated by TrueFoundry saved agent
  - `last_failure`: `null`
  - trace links: `1`
- Captured response header:
  - `x-tfy-feedback-target-id` was present
- Decoded feedback target:
  - `traceId`: `019e88d3d58b72289db404b486e0e151`
  - `spanId`: `1078a3517b71ad36`
  - `dataRoutingDestination`: `default`
- Stored trace:
  - `trace_id`: `019e88d3d58b72289db404b486e0e151`
  - `provisional`: `false`
  - `trace_source`: `feedback_target`
- Called `GET /incidents/inc_d21e416dc1dd/traces`:
  - response succeeded
  - traces count: `1`
  - lookup status: `found`
  - root span: `AgentResponse: halo/halo-vm-normal`
  - span count: `4`
  - model: `anthropic/claude-sonnet-4-6`
  - latency: `10805.75 ms`
  - guardrails triggered: `[]`
  - MCP/tool spans: `[]`
- Backend verification after code changes:
  - `pytest -q`: passed, `21 passed`
  - `ruff check app tests`: passed
  - `python -m compileall app tests`: passed

### 2026-06-02 Successful Saved-Agent Invocation

- Backend restart: succeeded
- Fresh server process command:
  - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Local route validation: passed
  - `GET /health`
  - `GET /readiness`
- Public ngrok validation: passed
- Saved-agent IDs were resolved one time with a PAT from:
  - `GET /api/svc/v1/agents?limit=100`
- Explicit non-secret saved-agent IDs were written to `apps/api/.env`:
  - `HALO_TRUEFOUNDRY_AGENT_ID_NORMAL=r92b8us4yrd6wtq6gqe6no2s`
  - `HALO_TRUEFOUNDRY_AGENT_ID_DEGRADED=yk772t05gwaxmt3r6ej4dcuj`
  - `HALO_TRUEFOUNDRY_AGENT_ID_BLACKOUT=jlmxjslw3lja29j4keo4ogj6`
- Backend fixes required for the live workspace:
  - TrueFoundry requests now send a browser-like `User-Agent`
  - `X-TFY-METADATA` values are serialized as strings
  - Agent Responses body includes `model` because the workspace has no load-balance
    rule configured
- Created incident through public URL: `inc_85e9b800dd17`
- Ran one workflow step through public URL:
  - resulting stage: `classify`
  - resulting mode: `normal`
  - current agent: `halo-normal`
  - current virtual model: `halo-vm-normal`
  - latest recommendation: updated by TrueFoundry saved agent
  - `last_failure`: `null`
  - trace links: `1`
- Stored trace/request ID:
  - `chatcmpl-eb87034e-c19c-4e30-a795-35c866cd1518`
  - marked provisional because no dedicated trace ID field was exposed
- Called `GET /incidents/inc_85e9b800dd17/traces`:
  - response succeeded
  - traces count: `1`
  - lookup status: `not_found`
  - live span enrichment: not found for the provisional response ID
- Backend verification after code changes:
  - `pytest -q`: passed, `18 passed`
  - `ruff check app tests`: passed
  - `python -m compileall app tests`: passed

### 2026-06-02 Agent App Endpoint Contract Smoke

- Backend restart: succeeded
- Fresh server process command:
  - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Local route validation: passed
  - `GET /health`
  - `GET /readiness`
  - `GET /health/summary`
  - `GET /openapi/incident-api.yaml`
  - `GET /openapi/runbooks-api.yaml`
- Public ngrok validation: passed
- Created incident through public URL: `inc_6f3fc188e267`
- Ran one workflow step through public URL:
  - resulting stage: `classify`
  - resulting mode: `degraded`
  - current agent after failure handling: `halo-degraded`
  - current virtual model after failure handling: `halo-vm-degraded`
  - trace links: `0`
- TrueFoundry saved-agent contract correction:
  - Halo now resolves agent app IDs from `GET /api/svc/v1/agent-versions`
  - Halo invokes `POST /api/llm/agent/{agent_app_id}/responses`
  - request body uses `iteration_limit`, `messages`, and `stream`
  - request body no longer sends `agent_name`
- TrueFoundry invocation result:
  - failed during agent app ID lookup
  - failed with HTTP `403`
  - response body prefix: `error code: 1010`
- Failure handling verified:
  - `truefoundry.invocation_failed` event present
  - `mode.changed` event present
  - `last_failure` populated
  - normal mode downgraded to degraded
- Called `GET /incidents/inc_6f3fc188e267/traces`:
  - response succeeded
  - traces count: `0`
  - live trace enrichment: not possible because no trace/request ID was returned
- Backend verification after code changes:
  - `pytest -q`: passed, `18 passed`
  - `ruff check app tests`: passed
  - `python -m compileall app tests`: passed

### 2026-06-02 Post-Restart Smoke With Agent Responses Path Correction

- Backend restart: succeeded
- Fresh server process command:
  - `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Local route validation: passed
  - `GET /health`
  - `GET /readiness`
  - `GET /health/summary`
  - `GET /openapi/incident-api.yaml`
  - `GET /openapi/runbooks-api.yaml`
- Public ngrok validation: passed
- Created incident through public URL: `inc_8867b01fe150`
- Ran one workflow step through public URL:
  - resulting stage: `classify`
  - resulting mode: `degraded`
  - current agent after failure handling: `halo-degraded`
  - current virtual model after failure handling: `halo-vm-degraded`
  - trace links: `0`
- `latest_recommendation` remained local deterministic output:
  - `Classify severity using service impact and customer visibility.`
- TrueFoundry invocation result:
  - attempted through `HALO_TRUEFOUNDRY_AGENT_RESPONSES_PATH`
  - failed with HTTP `403`
  - response body prefix: `error code: 1010`
- Failure handling verified:
  - `truefoundry.invocation_failed` event present
  - `mode.changed` event present
  - `last_failure` populated
  - normal mode downgraded to degraded
- Called `GET /incidents/inc_8867b01fe150/traces`:
  - response succeeded
  - traces count: `0`
  - live trace enrichment: not possible because no trace/request ID was returned
- Backend verification after code/test isolation changes:
  - `pytest -q`: passed, `14 passed`
  - `ruff check app tests`: passed
  - `python -m compileall app tests`: passed

### 2026-06-02 TrueFoundry Env Smoke

- Backend restart: succeeded
- Local route validation: passed
  - `GET /health`
  - `GET /readiness`
  - `GET /health/summary`
  - `GET /openapi/incident-api.yaml`
  - `GET /openapi/runbooks-api.yaml`
- Public ngrok validation: passed
- Created incident through public URL: `inc_89839005acfc`
- Ran one workflow step through public URL:
  - resulting stage: `classify`
  - resulting mode: `degraded`
  - current agent after failure handling: `halo-degraded`
  - current virtual model after failure handling: `halo-vm-degraded`
  - trace links: `0`
- `latest_recommendation` remained local deterministic output:
  - `Classify severity using service impact and customer visibility.`
- TrueFoundry invocation result:
  - attempted
  - failed with HTTP `403`
  - response body prefix: `error code: 1010`
- Failure handling verified:
  - `truefoundry.invocation_failed` event present
  - `mode.changed` event present
  - `last_failure` populated
  - normal mode downgraded to degraded
- Called `GET /incidents/inc_89839005acfc/traces`:
  - response succeeded
  - traces count: `0`
  - live trace enrichment: not possible because no trace/request ID was returned

Additional direct probes using the same configured token/base URL also returned HTTP
`403` with `error code: 1010`:

- `POST /api/llm/agent/responses`
- `GET /api/svc/v1/agents`
- `GET /api/svc/v1/spans/query`

Backend correction applied after this smoke:

- `HALO_TRUEFOUNDRY_AGENT_RESPONSES_PATH=/api/llm/agent/responses`
- The wrapper now builds the Agent Responses URL from the configured base URL plus this
  documented path.

### Earlier Public Tunnel Smoke

- Created incident through public URL: `inc_ac790296e4af`
- Ran one workflow step through public URL:
  - resulting stage: `classify`
  - mode: `normal`
  - trace links: `1`
- Called `GET /incidents/inc_ac790296e4af/traces`:
  - response succeeded
  - lookup status: `disabled`

Trace lookup was disabled during the earlier smoke because live TrueFoundry settings
were not available then.

## TrueFoundry Credentials / Tooling Check

Unavailable in this environment:

- `tfy` CLI
- Docker CLI
- `TFY_HOST`
- `TFY_API_KEY`
- `TRUEFOUNDRY_*`

Now available in `apps/api/.env`:

- `HALO_TRUEFOUNDRY_BASE_URL`
- `HALO_TRUEFOUNDRY_VIRTUAL_ACCOUNT_TOKEN`
- `HALO_TRUEFOUNDRY_ENABLED`
- `HALO_TRUEFOUNDRY_TRACES_ENABLED`

Available:

- `ngrok` with local config

## Live TrueFoundry Registration Status

No new live TrueFoundry objects were created from this environment because API access
to the configured TrueFoundry base URL is blocked with HTTP `403` / `error code: 1010`.

### MCP Servers

- `incident-api`: not registered
- `runbooks-api`: not registered

MCP server IDs/FQNs: unavailable.

### Virtual MCP Servers

- `halo-observe`: not created
- `halo-act`: not created

Virtual MCP server IDs/FQNs: unavailable.

### Saved Agents

- `halo-normal`: not attached/updated in live workspace
- `halo-degraded`: not attached/updated in live workspace
- `halo-blackout`: not attached/updated in live workspace

Saved agent IDs/FQNs: unavailable.

### Guardrails

- `halo-guardrails`: not attached in live workspace
- Exact live guardrail field names: not confirmed because workspace access is missing

## Exact Blockers

1. No durable deployment target or deployment CLI credentials are available.
2. TrueFoundry API access from this environment is blocked by HTTP `403` /
   `error code: 1010` for both Agent Responses and control-plane API paths.
3. No logged-in `tfy` CLI is available.
4. No confirmed API access to create OpenAPI MCP servers, virtual MCP servers,
   saved-agent attachments, or guardrail policies.
5. The ngrok URL is temporary and should not be used as a stable MCP registration URL.

## Exact Next Commands

Use these once a permanent public deployment target is available:

```bash
docker build -f apps/api/Dockerfile -t halo-api:latest .
```

Deploy the image with environment from:

```text
infra/deploy/backend.env.example
```

Validate the deployed public API:

```bash
export HALO_PUBLIC_API_BASE_URL=https://<permanent-halo-api-url>
./infra/deploy/validate-public-api.sh
```

Then register OpenAPI MCP servers in TrueFoundry:

1. Go to AI Gateway > MCP Servers.
2. Add Server.
3. Select From OpenAPI spec.
4. Register `incident-api`.
5. Use spec URL:
   - `https://<permanent-halo-api-url>/openapi/incident-api.yaml`
6. Set OpenAPI Server URL:
   - `https://<permanent-halo-api-url>`
7. Register `runbooks-api`.
8. Use spec URL:
   - `https://<permanent-halo-api-url>/openapi/runbooks-api.yaml`
9. Set OpenAPI Server URL:
   - `https://<permanent-halo-api-url>`

Create virtual MCP servers:

1. Create `halo-observe`.
2. Select read-only tools from `incident-api` and `runbooks-api`.
3. Exclude `failNextCall`, `delayNextCall`, and `returnBadPayload`.
4. Create `halo-act`.
5. Attach only approved low-risk GitHub/Slack write tools after those servers exist.

Attach saved agents:

1. `halo-normal`: `halo-vm-normal`, `halo-observe`, `halo-act`, iteration limit `5`.
2. `halo-degraded`: `halo-vm-degraded`, `halo-observe`, iteration limit `3`.
3. `halo-blackout`: `halo-vm-degraded` or `bedrock-nova-micro-fast`,
   `halo-observe` or no tools, iteration limit `2`.

Update backend env:

```bash
HALO_TRUEFOUNDRY_ENABLED=true
HALO_TRUEFOUNDRY_BASE_URL=<agent gateway base url>
HALO_TRUEFOUNDRY_VIRTUAL_ACCOUNT_TOKEN=<virtual account token>
HALO_TRUEFOUNDRY_TRACES_ENABLED=true
HALO_TRUEFOUNDRY_TRACES_BASE_URL=<control plane or traces base url>
HALO_TRUEFOUNDRY_TRACES_QUERY_PATH=/api/svc/v1/spans/query
HALO_TRUEFOUNDRY_TRACES_DATA_ROUTING_DESTINATION=default
```

## Guardrail Proof Attempt - 2026-06-02

Current live status:

- Saved-agent invocation is working.
- Bedrock-backed model spans are working.
- `halo-observe` MCP tool spans are working.
- Trace correlation and span enrichment are working.

Backend support added:

- `HALO_TRUEFOUNDRY_GUARDRAILS`
- When set, Halo sends the value as the documented `X-TFY-GUARDRAILS` header on
  Agent Responses calls.
- The value is JSON-normalized before sending so malformed local config fails before
  reaching TrueFoundry.

Live guardrail probe:

- Attempted selector: `halo-guardrails/secrets-detection`
- Header shape:

```json
{
  "llm_input_guardrails": ["halo-guardrails/secrets-detection"],
  "llm_output_guardrails": [],
  "mcp_tool_pre_invoke_guardrails": [],
  "mcp_tool_post_invoke_guardrails": []
}
```

Result:

- TrueFoundry returned HTTP `422`.
- Error message: `Guardrail integration halo-guardrails/secrets-detection not found`
- No trace-visible guardrail proof was produced because the guardrail integration does
  not exist in the live workspace yet.

Exact next UI setup:

1. In TrueFoundry, open AI Gateway > Guardrails.
2. Create or select guardrail group `halo-guardrails`.
3. Add TrueFoundry built-in `Secrets Detection`.
4. Configure it as `mutate` for demo-safe redaction, or `validate` if the demo should
   visibly block the request.
5. Name the integration `secrets-detection`.
6. Copy the integration FQN and confirm it is exactly
   `halo-guardrails/secrets-detection`, or update `HALO_TRUEFOUNDRY_GUARDRAILS` to
   the copied FQN.
7. For MCP visibility, attach the same selector under
   `mcp_tool_post_invoke_guardrails` in `HALO_TRUEFOUNDRY_GUARDRAILS`.
8. Restart the Halo API and rerun a tool-heavy incident scenario.

Suggested demo trigger:

- Scenario: `guardrail-secret-redaction-smoke`
- Incident summary should include a fake key such as
  `sk-demo1234567890demo1234567890demo1234567890`.
- If MCP post-invoke is selected, use a Halo observe tool result containing a fake
  key instead of relying on model output.

## Guardrail Visible Trace Proof - 2026-06-03

Live selector:

- `halo-guardrails/secrets-detection`

Backend configuration:

```bash
HALO_TRUEFOUNDRY_GUARDRAILS={"llm_input_guardrails":["halo-guardrails/secrets-detection"]}
```

Code support added:

- Halo now persists trace IDs returned on failed TrueFoundry Agent Responses calls
  when the failure response includes trace headers.
- This is required for validate/block guardrails because the agent call returns HTTP
  `422` instead of a normal response body.

Proof run:

- Incident id: `inc_95ec72a3a5a5`
- Scenario: `guardrail-visible-single-secret`
- Result: invocation blocked by input guardrail
- Halo mode after failure: `degraded`
- Persisted trace id: `019e8ad0e767720dbf45dd7b3cd777aa`
- Persisted span id from feedback target: `801fa85c84a2f036`
- Trace lookup status after ingestion delay: `found`

Trace summary:

- `root_span_name`: `AgentResponse: halo/halo-vm-normal`
- `status`: `error`
- `span_count`: `55`
- `model_name`: `aws-bedrock/us.anthropic.claude-opus-4-6-v1`
- `guardrails_triggered`:
  - `halo-guardrails/secrets-detection`
  - `halo:guardrail-config-group:halo-guardrails:guardrail-config:secrets-detection`

Observed guardrail span:

- Span name: `Guardrail: halo-guardrails/secrets-detection`
- Scope: input
- Result: `flag`
- Output summary: detected two potential secret findings in the incident input.

Remaining follow-up:

- `halo-vm-normal` still resolves to Bedrock Opus in this trace. If Sonnet is still
  required for the final demo, update the virtual model route in TrueFoundry and rerun
  the smoke.

## Jaguar Live Approval Proof - 2026-06-05

Halo-to-Jaguar approval bridge:

- `HALO_JAGUAR_MCP_URL` configured to `https://www.jaguaralpha.xyz/api/mcp`
- Live Jaguar MCP API key configured in Halo backend
- Live Jaguar operator secret configured in Halo backend

Proof incident:

- Incident id: `inc_ae2a13368c47`
- Product: `jaguar`
- Prepared Jaguar action id: `cmq0u17ba000004jme5kju2vd`
- Action type: `Worker Restart`
- Risk: `Medium`

Approval result:

- Halo `POST /incidents/inc_ae2a13368c47/approve` succeeded
- Native Halo approval moved from `pending` to `approved`
- Jaguar external response:
  `APPROVED action_request cmq0u17ba000004jme5kju2vd (worker_restart) — now queued for ops-runner.`

Jaguar live verification after approval:

- `get_recent_status_events` showed:
  `action_executed · ops-runner — worker_restart executed`
- Execution timestamp:
  `2026-06-06T03:18:05.669Z`

Post-action product state:

- `get_worker_status`: `DEGRADED`
- Heartbeat fresh:
  `2026-06-06T03:22:35.787Z (8s ago)`
- Worker process is alive after restart
- `get_ingestion_diagnostics` still shows all four streams at:
  `events: 0 · last: never`
- Recent operational events still show repeated:
  `AUTHENTICATION_ERROR / INVALID_TOKEN`

Root-cause conclusion:

- Restart fixed process liveness, but did not restore ingestion.
- The real issue is upstream stream authentication failure, not worker uptime.
- The next recovery step is GoldRush token / credential rotation or secrets-store
  correction on Jaguar, followed by another controlled restart or reconnect.

Demo significance:

- Halo proved real-product investigation through Jaguar MCP
- Halo surfaced a real approval gate for a risky action
- Halo executed a real VPS-backed recovery action through Jaguar ops-runner
- The action outcome produced new evidence that narrowed the root cause from
  `worker offline` to `credential invalidation`

## Clean Jaguar Demo Seed - 2026-06-06

Purpose:

- Create one UI-clean incident that preserves the real Jaguar approval proof, real
  trace, and real root-cause conclusion without requiring live operator actions on
  stage.

Seeded incident:

- Incident id: `inc_471c61c7a533`
- Title:
  `Jaguar worker offline after recent deploy - clean demo proof`
- Product: `jaguar`
- Environment: `production`
- Stage: `monitor`
- Mode: `normal`

Included proof:

- Real Jaguar action id:
  `cmq0u17ba000004jme5kju2vd`
- Native Halo approval status: `approved`
- Jaguar external status: `executed`
- Real TrueFoundry trace id:
  `019e97822312766daef28a9823b35178`
- Trace lookup status on the seeded incident: `found`

UI intent:

- `Halo's read` shows the clean final narrative:
  restart succeeded, ingestion still degraded, root cause is GoldRush credential
  invalidation
- `Trace evidence` shows real model routing, guardrails, and Jaguar MCP tool spans
- `Approval gate` shows the executed Jaguar action cleanly, not as pending
- `Event timeline` shows the full arc:
  incident created -> investigation -> approval -> external action executed ->
  verification completed
