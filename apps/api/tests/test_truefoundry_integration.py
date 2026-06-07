import base64
import json
import os
from pathlib import Path

TEST_DB = Path("test_halo_pytest.db")
os.environ["HALO_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["HALO_TRUEFOUNDRY_ENABLED"] = "false"
os.environ["HALO_TRUEFOUNDRY_TRACES_ENABLED"] = "false"
os.environ["HALO_TRUEFOUNDRY_AGENT_ID_NORMAL"] = ""
os.environ["HALO_TRUEFOUNDRY_AGENT_ID_DEGRADED"] = ""
os.environ["HALO_TRUEFOUNDRY_AGENT_ID_BLACKOUT"] = ""

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.incident import Incident, IncidentMode, IncidentSeverity  # noqa: E402
from app.repositories.incidents import IncidentRepository  # noqa: E402
from app.schemas.incident import IncidentRunRequest  # noqa: E402
from app.services.jaguar_actions import (  # noqa: E402
    get_jaguar_action_client,
    parse_prepared_jaguar_actions,
)
from app.services.truefoundry import (  # noqa: E402
    TrueFoundryAgentService,
    TrueFoundryInvocationError,
    TrueFoundryInvocationResult,
    TrueFoundryTraceCandidate,
    build_agent_messages,
    build_truefoundry_headers,
    decode_feedback_target,
    extract_agent_app_ids_by_name,
    extract_trace_candidate,
    get_truefoundry_service,
    normalize_guardrails_header,
    parse_agent_response_body,
)


class DisabledFakeTrueFoundry:
    invoked = False

    def should_invoke(self) -> bool:
        return False

    def invoke(self, incident: Incident, run_request: IncidentRunRequest) -> None:
        self.invoked = True
        raise AssertionError("disabled TrueFoundry service should not be invoked")


class SuccessFakeTrueFoundry:
    def should_invoke(self) -> bool:
        return True

    def invoke(
        self, incident: Incident, run_request: IncidentRunRequest
    ) -> TrueFoundryInvocationResult:
        return TrueFoundryInvocationResult(
            agent_name="halo-normal",
            agent_app_id="agent-app-normal",
            response={"trace_id": "tfy-trace-001", "recommendation": "Use TFY recommendation."},
            recommendation="Use TFY recommendation.",
            trace=TrueFoundryTraceCandidate(trace_id="tfy-trace-001", source="trace_id"),
        )


class FailureFakeTrueFoundry:
    def should_invoke(self) -> bool:
        return True

    def invoke(self, incident: Incident, run_request: IncidentRunRequest) -> None:
        raise TrueFoundryInvocationError("mock TrueFoundry outage")


class GuardrailFailureFakeTrueFoundry:
    def should_invoke(self) -> bool:
        return True

    def invoke(self, incident: Incident, run_request: IncidentRunRequest) -> None:
        raise TrueFoundryInvocationError(
            "mock guardrail block",
            trace=TrueFoundryTraceCandidate(
                trace_id="tfy-guardrail-trace",
                source="feedback_target",
                metadata={"feedback_span_id": "span-guardrail"},
            ),
        )


class PreparedActionFakeTrueFoundry:
    def should_invoke(self) -> bool:
        return True

    def invoke(
        self, incident: Incident, run_request: IncidentRunRequest
    ) -> TrueFoundryInvocationResult:
        recommendation = "\n".join(
            [
                "### Incident Summary & Actions Taken",
                "DRAFTED WORKER RESTART "
                "(action_request cmq0u17ba000004jme5kju2vd, status: proposed, risk: medium)",
                "Reason: worker streams are stale after GoldRush token auth failure.",
                "→ Awaiting operator approval (medium risk).",
            ]
        )
        return TrueFoundryInvocationResult(
            agent_name="halo-normal",
            agent_app_id="agent-app-normal",
            response={"id": "response-with-action"},
            recommendation=recommendation,
            trace=TrueFoundryTraceCandidate(trace_id="tfy-trace-action", source="trace_id"),
        )


class FakeJaguarActionClient:
    def __init__(self) -> None:
        self.calls = []

    def resolve_approval(self, approval, approved: bool, note: str | None) -> str:
        self.calls.append(
            {
                "external_action_id": approval.external_action_id,
                "approved": approved,
                "note": note,
            }
        )
        return f"APPROVED action_request {approval.external_action_id}"


def test_metadata_headers_and_agent_input_are_deterministic() -> None:
    incident = Incident(
        id="inc_headers",
        title="Checkout API elevated 5xx",
        severity=IncidentSeverity.SEV1,
        environment="prod",
        product="example-product",
        mode=IncidentMode.DEGRADED,
        summary="Header test",
    )
    incident.stage = "gather_evidence"
    run_request = IncidentRunRequest(scenario="bad-deploy", demo_run=True)
    integration_settings = Settings(
        truefoundry_virtual_account_token="secret-token",
        truefoundry_base_url="https://gateway.example.test",
        truefoundry_enabled=True,
        truefoundry_guardrails=None,
    )

    headers = build_truefoundry_headers(incident, run_request, integration_settings)
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["Content-Type"] == "application/json"
    assert json.loads(headers["X-TFY-LOGGING-CONFIG"]) == {"enabled": True}
    assert "X-TFY-GUARDRAILS" not in headers
    assert json.loads(headers["X-TFY-METADATA"]) == {
        "demo_run": "true",
        "environment": "prod",
        "incident_id": "inc_headers",
        "mode": "degraded",
        "product": "example-product",
        "scenario": "bad-deploy",
        "stage": "gather_evidence",
    }
    assert headers["X-TFY-METADATA"] == (
        '{"demo_run":"true","environment":"prod","incident_id":"inc_headers",'
        '"mode":"degraded","product":"example-product","scenario":"bad-deploy",'
        '"stage":"gather_evidence"}'
    )

    messages = build_agent_messages(incident, run_request)
    assert messages[0]["role"] == "system"
    assert "call at least two relevant Jaguar observe tools" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    content = json.loads(messages[1]["content"])
    assert content["incident"]["title"] == "Checkout API elevated 5xx"
    assert content["workflow"]["stage"] == "gather_evidence"
    assert content["run"] == {"demo_run": True, "scenario": "bad-deploy"}


def test_guardrails_header_is_configurable_and_deterministic() -> None:
    incident = Incident(
        id="inc_guardrails",
        title="Secret redaction proof",
        severity=IncidentSeverity.SEV2,
        environment="staging",
        product="halo",
        summary="Guardrail header test",
    )
    run_request = IncidentRunRequest(scenario="guardrail-secret-redaction", demo_run=True)
    integration_settings = Settings(
        truefoundry_virtual_account_token="secret-token",
        truefoundry_base_url="https://gateway.example.test",
        truefoundry_enabled=True,
        truefoundry_guardrails=(
            '{"mcp_tool_post_invoke_guardrails":["halo-guardrails/secrets-detection"],'
            '"llm_output_guardrails":[],"llm_input_guardrails":[]}'
        ),
    )

    headers = build_truefoundry_headers(incident, run_request, integration_settings)

    assert headers["X-TFY-GUARDRAILS"] == (
        '{"llm_input_guardrails":[],"llm_output_guardrails":[],'
        '"mcp_tool_post_invoke_guardrails":["halo-guardrails/secrets-detection"]}'
    )


def test_guardrails_header_rejects_invalid_json() -> None:
    try:
        normalize_guardrails_header("not-json")
    except TrueFoundryInvocationError as exc:
        assert "must be JSON" in str(exc)
    else:
        raise AssertionError("invalid guardrails header should fail")


def test_agent_app_ids_resolve_by_manifest_name_from_agent_versions(
    monkeypatch,
) -> None:
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return FakeHTTPResponse(
            {
                "items": [
                    {"manifest": {"name": "halo-normal"}, "agentAppId": "app-normal"},
                    {"manifest": {"name": "halo-degraded"}, "agent_app": {"id": "app-degraded"}},
                ]
            }
        )

    monkeypatch.setattr("app.services.truefoundry.urlopen", fake_urlopen)
    service = TrueFoundryAgentService(
        Settings(
            truefoundry_enabled=True,
            truefoundry_base_url="https://halo.truefoundry.cloud",
            truefoundry_virtual_account_token="secret-token",
            truefoundry_agent_name_normal="halo-normal",
        )
    )

    assert service.resolve_agent_app_id(IncidentMode.NORMAL) == "app-normal"
    assert service.resolve_agent_app_id(IncidentMode.DEGRADED) == "app-degraded"
    assert len(requests) == 1
    assert requests[0][0].full_url == (
        "https://halo.truefoundry.cloud/api/svc/v1/agent-versions"
    )


def test_agent_app_endpoint_uses_path_id_and_omits_agent_name(monkeypatch) -> None:
    captured = []

    def fake_urlopen(request, timeout):
        body = json.loads(request.data.decode())
        captured.append((request.full_url, body, dict(request.headers), timeout))
        return FakeHTTPResponse(
            {"id": "response-123", "output_text": "Agent says classify this as SEV2."}
        )

    monkeypatch.setattr("app.services.truefoundry.urlopen", fake_urlopen)
    service = TrueFoundryAgentService(
        Settings(
            truefoundry_enabled=True,
            truefoundry_base_url="https://halo.truefoundry.cloud/",
            truefoundry_virtual_account_token="secret-token",
            truefoundry_agent_id_normal="agent-app-normal",
            truefoundry_request_timeout_seconds=7,
        )
    )
    incident = Incident(
        id="inc_agent_endpoint",
        title="Checkout API elevated 5xx",
        severity=IncidentSeverity.SEV2,
        environment="staging",
        product="halo",
        summary="Endpoint test",
    )

    result = service.invoke(
        incident,
        IncidentRunRequest(scenario="endpoint-contract", demo_run=True),
    )

    assert result is not None
    assert captured[0][0] == (
        "https://halo.truefoundry.cloud/api/llm/agent/agent-app-normal/responses"
    )
    assert captured[0][1]["iteration_limit"] == 5
    assert captured[0][1]["mcp_servers"] == [
        {"name": "jaguar-observe", "enable_all_tools": True},
        {"name": "jaguar-act", "enable_all_tools": True},
    ]
    assert captured[0][1]["model"] == "halo/halo-vm-normal"
    assert captured[0][1]["stream"] is False
    assert "messages" in captured[0][1]
    assert "agent_name" not in captured[0][1]
    assert captured[0][3] == 7
    assert result.recommendation == "Agent says classify this as SEV2."
    assert result.trace is not None
    assert result.trace.trace_id == "response-123"
    assert result.trace.provisional is True
    assert json.loads(captured[0][2]["X-tfy-logging-config"]) == {"enabled": True}


def test_degraded_agent_uses_observe_without_act_tools(monkeypatch) -> None:
    captured = []

    def fake_urlopen(request, timeout):
        captured.append(json.loads(request.data.decode()))
        return FakeHTTPResponse({"id": "response-123", "output_text": "Degraded response."})

    monkeypatch.setattr("app.services.truefoundry.urlopen", fake_urlopen)
    service = TrueFoundryAgentService(
        Settings(
            truefoundry_enabled=True,
            truefoundry_base_url="https://halo.truefoundry.cloud/",
            truefoundry_virtual_account_token="secret-token",
            truefoundry_agent_id_degraded="agent-app-degraded",
        )
    )
    incident = Incident(
        id="inc_degraded_endpoint",
        title="Jaguar ingestion stale",
        severity=IncidentSeverity.SEV2,
        environment="production",
        product="jaguar",
        summary="Worker is alive but ingestion is stale.",
        mode=IncidentMode.DEGRADED,
    )

    result = service.invoke(
        incident,
        IncidentRunRequest(scenario="degraded-jaguar-contract", demo_run=True),
    )

    assert result is not None
    assert captured[0]["iteration_limit"] == 3
    assert captured[0]["mcp_servers"] == [
        {"name": "jaguar-observe", "enable_all_tools": True}
    ]
    assert captured[0]["model"] == "halo/halo-vm-degraded"


def test_feedback_target_decode_extracts_trace_and_span_ids() -> None:
    feedback_target = _b64url_json(
        {
            "target": {
                "traceId": "trace-from-feedback",
                "spanId": "span-from-feedback",
            }
        }
    )

    decoded = decode_feedback_target(feedback_target)

    assert decoded.trace_id == "trace-from-feedback"
    assert decoded.span_id == "span-from-feedback"
    assert decoded.decode_error is None


def test_feedback_target_header_capture_and_trace_priority() -> None:
    feedback_target = _b64url_json(
        {
            "traceId": "trace-from-feedback",
            "spanId": "span-from-feedback",
        }
    )

    feedback_trace = extract_trace_candidate(
        {"response_id": "response-fallback"},
        {"x-tfy-feedback-target-id": feedback_target},
    )
    assert feedback_trace is not None
    assert feedback_trace.trace_id == "trace-from-feedback"
    assert feedback_trace.source == "feedback_target"
    assert feedback_trace.provisional is False
    assert feedback_trace.metadata is not None
    assert feedback_trace.metadata["feedback_span_id"] == "span-from-feedback"
    assert feedback_trace.metadata["feedback_target_id"] == feedback_target

    explicit_trace = extract_trace_candidate(
        {"trace_id": "explicit-trace"},
        {"x-tfy-feedback-target-id": feedback_target},
    )
    assert explicit_trace is not None
    assert explicit_trace.trace_id == "explicit-trace"
    assert explicit_trace.source == "trace_id"

    request_id_trace = extract_trace_candidate(
        {"id": "chatcmpl-last"},
        {"x-request-id": "request-before-chat"},
    )
    assert request_id_trace is not None
    assert request_id_trace.trace_id == "request-before-chat"
    assert request_id_trace.source == "response_or_request_id"


def test_undecodable_feedback_target_is_kept_in_metadata() -> None:
    trace = extract_trace_candidate(
        {"id": "chatcmpl-fallback"},
        {"x-tfy-feedback-target-id": "not-json-or-base64"},
    )

    assert trace is not None
    assert trace.trace_id == "chatcmpl-fallback"
    assert trace.source == "chat_completion_id"
    assert trace.provisional is True
    assert trace.metadata is not None
    assert trace.metadata["feedback_target_id"] == "not-json-or-base64"
    assert "feedback_target_decode_error" in trace.metadata


def test_sse_agent_response_extracts_text_and_provisional_id() -> None:
    parsed = parse_agent_response_body(
        "\n".join(
            [
                'data: {"id":"response-sse-1","output_text":"First chunk"}',
                'data: {"text":"Second chunk"}',
                "data: [DONE]",
            ]
        ),
        {"Content-Type": "text/event-stream"},
    )

    assert parsed["id"] == "response-sse-1"
    assert parsed["output_text"] == "First chunk\nSecond chunk"


def test_agent_version_mapping_helper_accepts_common_id_shapes() -> None:
    assert extract_agent_app_ids_by_name(
        {
            "data": [
                {"manifest": {"name": "halo-normal"}, "applicationId": "app-normal"},
                {"manifest": {"name": "halo-blackout"}, "application": {"id": "app-blackout"}},
            ]
        }
    ) == {"halo-normal": "app-normal", "halo-blackout": "app-blackout"}


def test_jaguar_action_parser_extracts_worker_restart_request() -> None:
    actions = parse_prepared_jaguar_actions(
        "DRAFTED WORKER RESTART "
        "(action_request cmq0u17ba000004jme5kju2vd, status: proposed, risk: medium)"
    )

    assert len(actions) == 1
    assert actions[0].action_id == "cmq0u17ba000004jme5kju2vd"
    assert actions[0].action_type == "worker_restart"
    assert actions[0].title == "Worker Restart"
    assert actions[0].risk == "Medium"
    assert actions[0].external_status == "proposed"


def test_jaguar_action_parser_ignores_evidence_tokens_and_extracts_action_row() -> None:
    actions = parse_prepared_jaguar_actions(
        """
        Use `get_worker_status`, `get_ingestion_diagnostics`, and `get_recent_deploys`.
        Root cause is `AUTHENTICATION_ERROR / INVALID_TOKEN`; incident `inc_ae2a13368c47`.
        A `recovery_complete` event should appear after restart.

        | Action | ID | Status | Risk |
        | **Worker Restart** | `cmq0u17ba000004jme5kju2vd` | Awaiting operator approval | Medium |
        """
    )

    assert len(actions) == 1
    assert actions[0].action_id == "cmq0u17ba000004jme5kju2vd"
    assert actions[0].action_type == "worker_restart"
    assert actions[0].risk == "Medium"


def test_disabled_truefoundry_uses_local_workflow_without_invocation() -> None:
    fake = DisabledFakeTrueFoundry()
    app.dependency_overrides[get_truefoundry_service] = lambda: fake
    try:
        with TestClient(app) as client:
            incident_id = _create_incident(client)
            run = client.post(
                f"/incidents/{incident_id}/run",
                json={"scenario": "local-only", "demo_run": True},
            )
            assert run.status_code == 200
            incident = run.json()["incident"]
            assert incident["latest_recommendation"].startswith("Classify severity")
            assert all(
                event["type"] != "truefoundry.invocation_succeeded"
                for event in incident["events"]
            )
            assert len(incident["trace_links"]) == 1
            assert incident["trace_links"][0]["trace_id"].startswith("pending-")
            assert fake.invoked is False
    finally:
        app.dependency_overrides.clear()


def test_successful_truefoundry_invocation_updates_recommendation_and_trace() -> None:
    app.dependency_overrides[get_truefoundry_service] = lambda: SuccessFakeTrueFoundry()
    try:
        with TestClient(app) as client:
            incident_id = _create_incident(client)
            run = client.post(
                f"/incidents/{incident_id}/run",
                json={"scenario": "tfy-success", "demo_run": True},
            )
            assert run.status_code == 200
            incident = run.json()["incident"]
            assert incident["latest_recommendation"] == "Use TFY recommendation."
            assert incident["trace_links"][0]["trace_id"] == "tfy-trace-001"
            assert incident["trace_links"][0]["metadata"]["source"] == "truefoundry"
            assert incident["trace_links"][0]["metadata"]["provisional"] is False
            assert any(
                event["type"] == "truefoundry.invocation_succeeded"
                for event in incident["events"]
            )

        with Session(engine) as session:
            reloaded = IncidentRepository(session).get(incident_id)
            assert reloaded is not None
            assert reloaded.trace_links[0].trace_id == "tfy-trace-001"
            assert reloaded.trace_links[0].metadata["source"] == "truefoundry"
    finally:
        app.dependency_overrides.clear()


def test_prepared_jaguar_action_becomes_native_halo_approval() -> None:
    fake_jaguar = FakeJaguarActionClient()
    app.dependency_overrides[get_truefoundry_service] = lambda: PreparedActionFakeTrueFoundry()
    app.dependency_overrides[get_jaguar_action_client] = lambda: fake_jaguar
    try:
        with TestClient(app) as client:
            incident_id = _create_incident(client)
            run = client.post(
                f"/incidents/{incident_id}/run",
                json={"scenario": "jaguar-worker-offline", "demo_run": True},
            )
            assert run.status_code == 200
            incident = run.json()["incident"]
            assert incident["status"] == "waiting_for_approval"
            assert len(incident["approvals"]) == 1
            approval = incident["approvals"][0]
            assert approval["action_type"] == "jaguar:worker_restart"
            assert approval["external_system"] == "jaguar"
            assert approval["external_action_id"] == "cmq0u17ba000004jme5kju2vd"
            assert approval["external_status"] == "proposed"
            assert approval["risk"] == "Medium"
            assert approval["title"] == "Worker Restart"
            assert any(
                event["type"] == "approval.requested"
                and event["payload"]["external_action_id"] == "cmq0u17ba000004jme5kju2vd"
                for event in incident["events"]
            )

            approved = client.post(
                f"/incidents/{incident_id}/approve",
                json={"approval_id": approval["id"], "approved": True, "note": "demo approval"},
            )
            assert approved.status_code == 200
            approved_payload = approved.json()
            resolved = approved_payload["approval"]
            assert resolved["status"] == "approved"
            assert resolved["external_status"] == "approved"
            assert resolved["details"]["external_response"].startswith("APPROVED action_request")
            assert "### Approval outcome" in approved_payload["incident"]["latest_recommendation"]
            assert "Worker Restart" in approved_payload["incident"]["latest_recommendation"]
            assert "cmq0u17ba000004jme5kju2vd" in approved_payload["incident"]["latest_recommendation"]
            assert fake_jaguar.calls == [
                {
                    "external_action_id": "cmq0u17ba000004jme5kju2vd",
                    "approved": True,
                    "note": "demo approval",
                }
            ]
    finally:
        app.dependency_overrides.clear()


def test_failed_truefoundry_invocation_records_failure_and_downgrades() -> None:
    app.dependency_overrides[get_truefoundry_service] = lambda: FailureFakeTrueFoundry()
    try:
        with TestClient(app) as client:
            incident_id = _create_incident(client)
            run = client.post(
                f"/incidents/{incident_id}/run",
                json={"scenario": "tfy-failure", "demo_run": True},
            )
            assert run.status_code == 200
            incident = run.json()["incident"]
            assert incident["mode"] == "degraded"
            assert incident["current_agent"] == "halo-degraded"
            assert incident["last_failure"] == "mock TrueFoundry outage"
            event_types = [event["type"] for event in incident["events"]]
            assert "truefoundry.invocation_failed" in event_types
            assert "mode.changed" in event_types
            assert incident["checkpoints"][-1]["state"]["reason"] == (
                "truefoundry invocation failed"
            )
    finally:
        app.dependency_overrides.clear()


def test_failed_truefoundry_invocation_persists_failure_trace() -> None:
    app.dependency_overrides[get_truefoundry_service] = lambda: GuardrailFailureFakeTrueFoundry()
    try:
        with TestClient(app) as client:
            incident_id = _create_incident(client)
            run = client.post(
                f"/incidents/{incident_id}/run",
                json={"scenario": "guardrail-block", "demo_run": True},
            )
            assert run.status_code == 200
            incident = run.json()["incident"]
            assert incident["mode"] == "degraded"
            assert incident["last_failure"] == "mock guardrail block"
            assert incident["trace_links"][0]["trace_id"] == "tfy-guardrail-trace"
            assert incident["trace_links"][0]["metadata"]["failure"] is True
            assert incident["trace_links"][0]["metadata"]["trace_source"] == "feedback_target"
            assert incident["trace_links"][0]["metadata"]["feedback_span_id"] == "span-guardrail"
            failure_event = next(
                event
                for event in incident["events"]
                if event["type"] == "truefoundry.invocation_failed"
            )
            assert failure_event["payload"]["trace_id"] == "tfy-guardrail-trace"
    finally:
        app.dependency_overrides.clear()


def _create_incident(client: TestClient) -> str:
    created = client.post(
        "/incidents",
        json={
            "title": "Checkout API elevated 5xx",
            "severity": "sev1",
            "summary": "TrueFoundry integration test",
        },
    )
    assert created.status_code == 201
    return created.json()["incident"]["id"]


class FakeHTTPResponse:
    def __init__(
        self,
        body,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.body = body
        self.headers = headers or {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        if isinstance(self.body, str):
            return self.body.encode()
        return json.dumps(self.body).encode()


def _b64url_json(payload: dict) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return encoded.rstrip("=")
