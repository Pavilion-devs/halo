import os
from pathlib import Path

TEST_DB = Path("test_halo_pytest.db")
os.environ["HALO_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["HALO_TRUEFOUNDRY_ENABLED"] = "false"
os.environ["HALO_TRUEFOUNDRY_TRACES_ENABLED"] = "false"

import yaml  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.incident import TraceLink  # noqa: E402
from app.repositories.incidents import IncidentRepository  # noqa: E402
from app.services.truefoundry_traces import (  # noqa: E402
    TraceLookupError,
    TraceQueryWindow,
    TrueFoundryTraceService,
    build_spans_query_payload,
    get_trace_service,
    is_provisional_trace,
)


class LiveTraceService(TrueFoundryTraceService):
    def should_lookup(self) -> bool:
        return True

    def query_spans(
        self, trace_ids: list[str], query_window: TraceQueryWindow
    ) -> list[dict]:
        assert sorted(trace_ids) == ["response-provisional-001", "trace-live-ok"]
        assert query_window.start_time < query_window.end_time
        return [
            {
                "traceId": "trace-live-ok",
                "spanId": "root-1",
                "parentSpanId": "",
                "spanName": "ChatCompletion: halo-vm-normal",
                "durationNs": 123_000_000,
                "statusCode": "Ok",
                "spanAttributes": {
                    "tfy.span_type": "ChatCompletion",
                    "tfy.triggered_guardrail_fqns": ["guardrail-a"],
                },
            },
            {
                "traceId": "trace-live-ok",
                "spanId": "model-1",
                "parentSpanId": "root-1",
                "spanName": "Model: halo-vm-normal",
                "statusCode": "Ok",
                "spanAttributes": {
                    "tfy.span_type": "Model",
                    "tfy.model.name": "halo-vm-normal",
                    "tfy.model.metric.latency_in_ms": 111.5,
                },
            },
            {
                "traceId": "response-provisional-001",
                "spanId": "root-2",
                "parentSpanId": "",
                "spanName": "MCP call",
                "statusCode": "Ok",
                "spanAttributes": {
                    "tfy.mcp.server.name": "incident-api",
                    "tfy.mcp.tool.name": "getHealthSummary",
                },
            },
        ]


class FailingTraceService(TrueFoundryTraceService):
    def should_lookup(self) -> bool:
        return True

    def query_spans(
        self, trace_ids: list[str], query_window: TraceQueryWindow
    ) -> list[dict]:
        raise TraceLookupError("mock trace backend unavailable")


def test_trace_endpoint_disabled_returns_persisted_links_only() -> None:
    with TestClient(app) as client:
        incident_id = _create_incident_with_traces(client)
        response = client.get(f"/incidents/{incident_id}/traces")

    assert response.status_code == 200
    payload = response.json()
    assert payload["incident_id"] == incident_id
    assert payload["error"] is None
    assert [trace["lookup_status"] for trace in payload["traces"]] == ["disabled", "disabled"]
    assert payload["traces"][0]["trace_id"] == "trace-live-ok"
    assert payload["traces"][0]["provisional"] is False
    assert payload["traces"][1]["trace_id"] == "response-provisional-001"
    assert payload["traces"][1]["provisional"] is True
    assert payload["traces"][0]["live_summary"] is None


def test_trace_endpoint_enriches_with_mocked_live_lookup() -> None:
    app.dependency_overrides[get_trace_service] = lambda: LiveTraceService()
    try:
        with TestClient(app) as client:
            incident_id = _create_incident_with_traces(client)
            response = client.get(f"/incidents/{incident_id}/traces")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert [trace["lookup_status"] for trace in payload["traces"]] == ["found", "found"]
    assert payload["traces"][0]["live_summary"]["root_span_name"] == (
        "ChatCompletion: halo-vm-normal"
    )
    assert payload["traces"][0]["live_summary"]["model_name"] == "halo-vm-normal"
    assert payload["traces"][0]["live_summary"]["latency_ms"] == 111.5
    assert payload["traces"][0]["live_summary"]["guardrails_triggered"] == ["guardrail-a"]
    assert payload["traces"][1]["live_summary"]["mcp_tool_spans"][0]["server"] == "incident-api"


def test_trace_lookup_failure_returns_partial_data_safely() -> None:
    app.dependency_overrides[get_trace_service] = lambda: FailingTraceService()
    try:
        with TestClient(app) as client:
            incident_id = _create_incident_with_traces(client)
            response = client.get(f"/incidents/{incident_id}/traces")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] == "mock trace backend unavailable"
    assert payload["traces"][0]["lookup_status"] == "error"
    assert payload["traces"][1]["lookup_status"] == "error"
    assert payload["traces"][1]["error"] == "mock trace backend unavailable"
    assert payload["traces"][1]["trace_id"] == "response-provisional-001"


def test_provisional_trace_helper_uses_metadata_flag() -> None:
    assert is_provisional_trace(
        TraceLink(
            incident_id="inc_trace_helper",
            trace_id="response-id",
            metadata={"provisional": True},
        )
    )
    assert not is_provisional_trace(
        TraceLink(
            incident_id="inc_trace_helper",
            trace_id="trace-id",
            metadata={"provisional": False},
        )
    )


def test_openapi_specs_match_custom_api_registration_paths() -> None:
    incident_spec = _load_yaml("infra/openapi/incident-api.yaml")
    runbooks_spec = _load_yaml("infra/openapi/runbooks-api.yaml")

    assert set(incident_spec["paths"]) == {
        "/health/summary",
        "/deploys/recent",
        "/errors/top",
        "/incidents/{incident_id}/context",
        "/status/events/recent",
        "/demo/fail-next",
        "/demo/delay-next",
        "/demo/return-bad-payload",
    }
    assert incident_spec["paths"]["/incidents/{incident_id}/context"]["get"]["parameters"][0][
        "name"
    ] == "incident_id"
    assert set(runbooks_spec["paths"]) == {"/runbooks/search", "/runbooks/{slug}"}
    q_schema = runbooks_spec["paths"]["/runbooks/search"]["get"]["parameters"][0]["schema"]
    assert q_schema["minLength"] == 1


def test_registration_openapi_specs_are_served() -> None:
    with TestClient(app) as client:
        incident_spec = client.get("/openapi/incident-api.yaml")
        runbooks_spec = client.get("/openapi/runbooks-api.yaml")
        missing_spec = client.get("/openapi/unknown.yaml")

    assert incident_spec.status_code == 200
    assert "operationId: getHealthSummary" in incident_spec.text
    assert runbooks_spec.status_code == 200
    assert "operationId: searchRunbooks" in runbooks_spec.text
    assert missing_spec.status_code == 404


def test_spans_query_payload_uses_batch_trace_ids_and_config() -> None:
    query_window = TraceQueryWindow(
        start_time=_parse_utc("2026-06-02T00:00:00Z"),
        end_time=_parse_utc("2026-06-02T01:00:00Z"),
    )
    payload = build_spans_query_payload(
        ["trace-b", "trace-a", "trace-b"],
        query_window,
    )

    assert payload["traceIds"] == ["trace-a", "trace-b"]
    assert payload["dataRoutingDestination"] == "default"
    assert payload["startTime"] == "2026-06-02T00:00:00.000Z"
    assert payload["endTime"] == "2026-06-02T01:00:00.000Z"
    assert payload["sortDirection"] == "desc"
    assert payload["limit"] == 200


def _create_incident_with_traces(client: TestClient) -> str:
    created = client.post(
        "/incidents",
        json={
            "title": "Trace observability smoke",
            "severity": "sev2",
            "summary": "Trace endpoint test",
        },
    )
    assert created.status_code == 201
    incident_id = created.json()["incident"]["id"]
    with Session(engine) as session:
        repository = IncidentRepository(session)
        incident = repository.get(incident_id)
        assert incident is not None
        incident.trace_links.extend(
            [
                TraceLink(
                    incident_id=incident_id,
                    trace_id="trace-live-ok",
                    metadata={"source": "truefoundry", "provisional": False},
                ),
                TraceLink(
                    incident_id=incident_id,
                    trace_id="response-provisional-001",
                    metadata={"source": "truefoundry", "provisional": True},
                ),
            ]
        )
        repository.save(incident)
    return incident_id


def _load_yaml(path: str) -> dict:
    with Path("../../").joinpath(path).resolve().open() as handle:
        return yaml.safe_load(handle)


def _parse_utc(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00"))
