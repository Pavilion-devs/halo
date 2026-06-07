import base64
import binascii
import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen

from app.core.config import Settings, settings
from app.models.incident import Incident, IncidentMode, TraceLink
from app.schemas.incident import IncidentRunRequest


@dataclass
class TrueFoundryTraceCandidate:
    trace_id: str
    source: str
    provisional: bool = False
    metadata: dict[str, Any] | None = None


@dataclass
class TrueFoundryInvocationResult:
    agent_name: str
    agent_app_id: str
    response: dict[str, Any]
    recommendation: str | None = None
    trace: TrueFoundryTraceCandidate | None = None


class TrueFoundryInvocationError(RuntimeError):
    def __init__(
        self,
        message: str,
        trace: TrueFoundryTraceCandidate | None = None,
    ) -> None:
        super().__init__(message)
        self.trace = trace


class TrueFoundryAgentService:
    def __init__(self, integration_settings: Settings = settings) -> None:
        self.settings = integration_settings
        self._agent_app_ids_by_name: dict[str, str] | None = None

    def should_invoke(self) -> bool:
        return bool(
            self.settings.truefoundry_enabled
            and self.settings.truefoundry_base_url
            and self.settings.truefoundry_virtual_account_token
        )

    def select_agent_name(self, mode: IncidentMode) -> str:
        if mode == IncidentMode.DEGRADED:
            return self.settings.truefoundry_agent_name_degraded
        if mode == IncidentMode.BLACKOUT:
            return self.settings.truefoundry_agent_name_blackout
        return self.settings.truefoundry_agent_name_normal

    def select_model(self, mode: IncidentMode) -> str:
        if mode == IncidentMode.DEGRADED:
            return self.settings.truefoundry_model_degraded
        if mode == IncidentMode.BLACKOUT:
            return self.settings.truefoundry_model_blackout
        return self.settings.truefoundry_model_normal

    def resolve_agent_app_id(self, mode: IncidentMode) -> str:
        explicit_id = self._explicit_agent_app_id(mode)
        if explicit_id:
            return explicit_id

        agent_name = self.select_agent_name(mode)
        if self._agent_app_ids_by_name is None:
            self._agent_app_ids_by_name = self._fetch_agent_app_ids_by_name()
        agent_app_id = self._agent_app_ids_by_name.get(agent_name)
        if not agent_app_id:
            raise TrueFoundryInvocationError(
                f"TrueFoundry agent app id not found for saved agent {agent_name}"
            )
        return agent_app_id

    def invoke(
        self, incident: Incident, run_request: IncidentRunRequest
    ) -> TrueFoundryInvocationResult | None:
        if not self.should_invoke():
            return None

        agent_name = self.select_agent_name(incident.mode)
        agent_app_id = self.resolve_agent_app_id(incident.mode)
        request_body = {
            "iteration_limit": iteration_limit_for_mode(incident.mode),
            "mcp_servers": mcp_servers_for_mode(incident.mode, self.settings),
            "messages": build_agent_messages(incident, run_request),
            "model": self.select_model(incident.mode),
            "stream": False,
        }
        headers = build_truefoundry_headers(incident, run_request, self.settings)

        response_body, response_headers = self._post_agent_response(
            agent_app_id, request_body, headers
        )
        return TrueFoundryInvocationResult(
            agent_name=agent_name,
            agent_app_id=agent_app_id,
            response=response_body,
            recommendation=extract_recommendation(response_body),
            trace=extract_trace_candidate(response_body, response_headers),
        )

    def _post_agent_response(
        self, agent_app_id: str, body: dict[str, Any], headers: dict[str, str]
    ) -> tuple[dict[str, Any], dict[str, str]]:
        assert self.settings.truefoundry_base_url is not None
        url = (
            f"{self.settings.truefoundry_base_url.rstrip('/')}"
            f"/api/llm/agent/{quote(agent_app_id, safe='')}/responses"
        )
        request = Request(
            url=url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(  # noqa: S310 - URL is operator-configured service endpoint.
                request,
                timeout=self.settings.truefoundry_request_timeout_seconds,
            ) as response:
                raw_body = response.read().decode("utf-8", errors="replace")
                response_headers = dict(response.headers.items())
                response_body = parse_agent_response_body(raw_body, response_headers)
                if not isinstance(response_body, dict):
                    raise TrueFoundryInvocationError("TrueFoundry returned a non-object response")
                return response_body, response_headers
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            response_headers = dict(exc.headers.items())
            try:
                response_body = json.loads(detail) if detail else {}
            except json.JSONDecodeError:
                response_body = {}
            raise TrueFoundryInvocationError(
                f"TrueFoundry agent request failed with HTTP {exc.code}: {detail}",
                trace=extract_trace_candidate(response_body, response_headers),
            ) from exc
        except URLError as exc:
            raise TrueFoundryInvocationError(
                f"TrueFoundry agent request failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise TrueFoundryInvocationError("TrueFoundry agent request timed out") from exc
        except json.JSONDecodeError as exc:
            raise TrueFoundryInvocationError("TrueFoundry returned invalid JSON") from exc

    def _fetch_agent_app_ids_by_name(self) -> dict[str, str]:
        assert self.settings.truefoundry_base_url is not None
        url = (
            f"{self.settings.truefoundry_base_url.rstrip('/')}/"
            f"{self.settings.truefoundry_agent_versions_path.lstrip('/')}"
        )
        request = Request(
            url=url,
            headers=build_truefoundry_auth_headers(self.settings),
            method="GET",
        )
        try:
            with urlopen(  # noqa: S310 - URL is operator-configured service endpoint.
                request,
                timeout=self.settings.truefoundry_request_timeout_seconds,
            ) as response:
                raw_body = response.read().decode("utf-8", errors="replace")
                response_body = json.loads(raw_body) if raw_body else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise TrueFoundryInvocationError(
                f"TrueFoundry agent version lookup failed with HTTP {exc.code}: {detail}"
            ) from exc
        except URLError as exc:
            raise TrueFoundryInvocationError(
                f"TrueFoundry agent version lookup failed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise TrueFoundryInvocationError("TrueFoundry agent version lookup timed out") from exc
        except json.JSONDecodeError as exc:
            raise TrueFoundryInvocationError(
                "TrueFoundry agent version lookup returned invalid JSON"
            ) from exc

        return extract_agent_app_ids_by_name(response_body)

    def _explicit_agent_app_id(self, mode: IncidentMode) -> str | None:
        if mode == IncidentMode.DEGRADED:
            return self.settings.truefoundry_agent_id_degraded
        if mode == IncidentMode.BLACKOUT:
            return self.settings.truefoundry_agent_id_blackout
        return self.settings.truefoundry_agent_id_normal


def get_truefoundry_service() -> TrueFoundryAgentService:
    return TrueFoundryAgentService()


def build_truefoundry_metadata(
    incident: Incident, run_request: IncidentRunRequest
) -> dict[str, Any]:
    return {
        "demo_run": run_request.demo_run,
        "environment": incident.environment,
        "incident_id": incident.id,
        "mode": str(incident.mode),
        "product": incident.product,
        "scenario": run_request.scenario,
        "stage": str(incident.stage),
    }


def build_truefoundry_headers(
    incident: Incident,
    run_request: IncidentRunRequest,
    integration_settings: Settings = settings,
) -> dict[str, str]:
    headers = build_truefoundry_auth_headers(integration_settings)
    headers["X-TFY-METADATA"] = json.dumps(
        build_truefoundry_header_metadata(incident, run_request),
        sort_keys=True,
        separators=(",", ":"),
    )
    headers["X-TFY-LOGGING-CONFIG"] = json.dumps(
        {"enabled": True},
        sort_keys=True,
        separators=(",", ":"),
    )
    if integration_settings.truefoundry_guardrails:
        headers["X-TFY-GUARDRAILS"] = normalize_guardrails_header(
            integration_settings.truefoundry_guardrails
        )
    return headers


def normalize_guardrails_header(raw_guardrails: str) -> str:
    try:
        parsed = json.loads(raw_guardrails)
    except json.JSONDecodeError as exc:
        raise TrueFoundryInvocationError("TrueFoundry guardrails header must be JSON") from exc
    if not isinstance(parsed, dict):
        raise TrueFoundryInvocationError("TrueFoundry guardrails header must be a JSON object")
    return json.dumps(parsed, sort_keys=True, separators=(",", ":"))


def build_truefoundry_header_metadata(
    incident: Incident, run_request: IncidentRunRequest
) -> dict[str, str]:
    return {
        key: str(value).lower() if isinstance(value, bool) else str(value)
        for key, value in build_truefoundry_metadata(incident, run_request).items()
    }


def build_truefoundry_auth_headers(
    integration_settings: Settings = settings,
) -> dict[str, str]:
    token = integration_settings.truefoundry_virtual_account_token
    if not token:
        raise TrueFoundryInvocationError("TrueFoundry token is not configured")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": integration_settings.truefoundry_user_agent,
    }


def iteration_limit_for_mode(mode: IncidentMode) -> int:
    if mode == IncidentMode.DEGRADED:
        return 3
    if mode == IncidentMode.BLACKOUT:
        return 2
    return 5


def mcp_servers_for_mode(
    mode: IncidentMode,
    integration_settings: Settings = settings,
) -> list[dict[str, Any]]:
    servers: list[dict[str, Any]] = []

    if integration_settings.truefoundry_mcp_server_observe:
        servers.append(
            {
                "name": integration_settings.truefoundry_mcp_server_observe,
                "enable_all_tools": True,
            }
        )

    if mode == IncidentMode.NORMAL and integration_settings.truefoundry_mcp_server_act:
        servers.append(
            {
                "name": integration_settings.truefoundry_mcp_server_act,
                "enable_all_tools": True,
            }
        )

    return servers


def build_agent_messages(
    incident: Incident, run_request: IncidentRunRequest
) -> list[dict[str, str]]:
    payload = {
        "incident": {
            "id": incident.id,
            "title": incident.title,
            "summary": incident.summary,
            "environment": incident.environment,
            "product": incident.product,
            "severity": str(incident.severity),
            "status": str(incident.status),
        },
        "workflow": {
            "stage": str(incident.stage),
            "mode": str(incident.mode),
            "latest_recommendation": incident.latest_recommendation,
        },
        "run": {
            "scenario": run_request.scenario,
            "demo_run": run_request.demo_run,
        },
        "recent_events": [
            {
                "type": event.type,
                "payload": event.payload,
                "created_at": event.created_at.isoformat(),
            }
            for event in incident.events[-5:]
        ],
        "pending_approvals": [
            {
                "id": approval.id,
                "action_type": approval.action_type,
                "requested_at": approval.requested_at.isoformat(),
            }
            for approval in incident.approvals
            if str(approval.status) == "pending"
        ],
    }
    return [
        {
            "role": "system",
            "content": (
                "You are Halo, an incident commander for Jaguar's live ingestion and "
                "worker pipeline. If incident evidence is incomplete and Jaguar observe "
                "tools are available, call at least two relevant Jaguar observe tools "
                "before diagnosing or recommending remediation. Prioritize worker "
                "health, ingestion diagnostics, recent deploys, recent failures, status "
                "events, alerts, and runbook lookups. Use Jaguar act tools only to "
                "prepare approval-gated recovery actions such as worker restart plans, "
                "rollback plans, or incident updates. Do not ask for permission to use "
                "read-only Jaguar observe tools during demo runs."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(payload, sort_keys=True, separators=(",", ":")),
        }
    ]


def extract_recommendation(response_body: dict[str, Any]) -> str | None:
    candidates = [
        response_body.get("latest_recommendation"),
        response_body.get("recommendation"),
        response_body.get("output_text"),
        response_body.get("text"),
        response_body.get("content"),
        response_body.get("message"),
        _nested_get(response_body, ("choices", 0, "message", "content")),
        _nested_get(response_body, ("data", "output_text")),
        _nested_get(response_body, ("response", "recommendation")),
        _nested_get(response_body, ("response", "output_text")),
        _nested_get(response_body, ("response", "text")),
        _output_content_text(response_body),
    ]
    return next((value for value in candidates if isinstance(value, str) and value.strip()), None)


def extract_trace_candidate(
    response_body: dict[str, Any], response_headers: dict[str, str] | None = None
) -> TrueFoundryTraceCandidate | None:
    headers = {key.lower(): value for key, value in (response_headers or {}).items()}
    captured_headers = capture_trace_headers(headers)
    feedback_target = captured_headers.get("x-tfy-feedback-target-id")
    decoded_feedback = decode_feedback_target(feedback_target)
    trace_metadata = trace_metadata_from_headers(captured_headers, decoded_feedback)

    real_candidates = [
        response_body.get("trace_id"),
        response_body.get("traceId"),
        _nested_get(response_body, ("trace", "id")),
        _nested_get(response_body, ("trace", "trace_id")),
        _nested_get(response_body, ("metadata", "trace_id")),
        headers.get("x-tfy-trace-id"),
        headers.get("x-trace-id"),
    ]
    trace_id = next((value for value in real_candidates if isinstance(value, str) and value), None)
    if trace_id:
        return TrueFoundryTraceCandidate(
            trace_id=trace_id,
            source="trace_id",
            metadata=trace_metadata,
        )

    if decoded_feedback.trace_id:
        return TrueFoundryTraceCandidate(
            trace_id=decoded_feedback.trace_id,
            source="feedback_target",
            metadata=trace_metadata,
        )

    provisional_candidates = [
        response_body.get("response_id"),
        response_body.get("request_id"),
        response_body.get("responseId"),
        _nested_get(response_body, ("response", "id")),
        _nested_get(response_body, ("data", "id")),
        headers.get("x-request-id"),
        headers.get("x-tfy-request-id"),
    ]
    provisional_id = next(
        (value for value in provisional_candidates if isinstance(value, str) and value), None
    )
    if provisional_id:
        return TrueFoundryTraceCandidate(
            trace_id=provisional_id,
            source="response_or_request_id",
            provisional=True,
            metadata=trace_metadata,
        )

    chat_completion_id = response_body.get("id")
    if isinstance(chat_completion_id, str) and chat_completion_id:
        return TrueFoundryTraceCandidate(
            trace_id=chat_completion_id,
            source="chat_completion_id",
            provisional=True,
            metadata=trace_metadata,
        )
    return None


def trace_link_from_result(
    incident: Incident,
    run_request: IncidentRunRequest,
    result: TrueFoundryInvocationResult,
) -> TraceLink | None:
    if result.trace is None:
        return None
    return TraceLink(
        incident_id=incident.id,
        trace_id=result.trace.trace_id,
        metadata={
            "agent_name": result.agent_name,
            "agent_app_id": result.agent_app_id,
            "demo_run": run_request.demo_run,
            "mode": str(incident.mode),
            "provisional": result.trace.provisional,
            "scenario": run_request.scenario,
            "source": "truefoundry",
            "stage": str(incident.stage),
            "trace_source": result.trace.source,
            **(result.trace.metadata or {}),
        },
    )


def trace_link_from_failure(
    incident: Incident,
    run_request: IncidentRunRequest,
    error: TrueFoundryInvocationError,
) -> TraceLink | None:
    if error.trace is None:
        return None
    return TraceLink(
        incident_id=incident.id,
        trace_id=error.trace.trace_id,
        metadata={
            "agent_name": incident.current_agent,
            "demo_run": run_request.demo_run,
            "failure": True,
            "mode": str(incident.mode),
            "provisional": error.trace.provisional,
            "scenario": run_request.scenario,
            "source": "truefoundry",
            "stage": str(incident.stage),
            "trace_source": error.trace.source,
            **(error.trace.metadata or {}),
        },
    )


@dataclass
class DecodedFeedbackTarget:
    trace_id: str | None = None
    span_id: str | None = None
    decoded: dict[str, Any] | None = None
    decode_error: str | None = None


def capture_trace_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        name: value
        for name in (
            "x-tfy-feedback-target-id",
            "x-tfy-trace-id",
            "x-request-id",
            "x-tfy-request-id",
            "x-tfy-applied-rules",
        )
        if (value := headers.get(name))
    }


def decode_feedback_target(feedback_target: str | None) -> DecodedFeedbackTarget:
    if not feedback_target:
        return DecodedFeedbackTarget()

    raw_value = feedback_target.strip()
    candidates = [raw_value, unquote(raw_value)]
    parts = raw_value.split(".")
    if len(parts) >= 2:
        candidates.append(parts[1])

    last_error: str | None = None
    for candidate in dict.fromkeys(candidates):
        for decoded_text in _decode_feedback_candidate(candidate):
            try:
                decoded = json.loads(decoded_text)
            except json.JSONDecodeError as exc:
                last_error = str(exc)
                continue
            if isinstance(decoded, dict):
                return DecodedFeedbackTarget(
                    trace_id=_find_nested_string(decoded, ("traceId", "trace_id", "traceID")),
                    span_id=_find_nested_string(decoded, ("spanId", "span_id", "spanID")),
                    decoded=decoded,
                )
    return DecodedFeedbackTarget(decode_error=last_error or "unable to decode feedback target")


def trace_metadata_from_headers(
    captured_headers: dict[str, str],
    decoded_feedback: DecodedFeedbackTarget,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if captured_headers:
        metadata["truefoundry_response_headers"] = captured_headers

    feedback_target = captured_headers.get("x-tfy-feedback-target-id")
    if feedback_target:
        metadata["feedback_target_id"] = feedback_target
        if decoded_feedback.trace_id:
            metadata["feedback_trace_id"] = decoded_feedback.trace_id
        if decoded_feedback.span_id:
            metadata["feedback_span_id"] = decoded_feedback.span_id
        if decoded_feedback.decoded is not None:
            metadata["feedback_target_decoded"] = decoded_feedback.decoded
        if decoded_feedback.decode_error:
            metadata["feedback_target_decode_error"] = decoded_feedback.decode_error
    return metadata


def _nested_get(source: dict[str, Any], path: tuple[Any, ...]) -> Any:
    current: Any = source
    for key in path:
        if isinstance(key, int) and isinstance(current, list) and len(current) > key:
            current = current[key]
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _output_content_text(response_body: dict[str, Any]) -> str | None:
    output = response_body.get("output")
    if not isinstance(output, list):
        return None
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    return block["text"]
    return None


def parse_agent_response_body(raw_body: str, response_headers: dict[str, str]) -> dict[str, Any]:
    if not raw_body:
        return {}

    content_type = _header_value(response_headers, "content-type")
    if "text/event-stream" in content_type or _looks_like_sse(raw_body):
        return parse_sse_agent_response(raw_body)
    return json.loads(raw_body)


def parse_sse_agent_response(raw_body: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    text_parts: list[str] = []
    response_id: str | None = None
    trace_id: str | None = None

    for line in raw_body.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            text_parts.append(data)
            continue
        if isinstance(event, dict):
            events.append(event)
            response_id = response_id or _event_string(event, ("id", "response_id", "request_id"))
            trace_id = trace_id or _event_string(event, ("trace_id", "traceId"))
            text = extract_recommendation(event)
            if text:
                text_parts.append(text)
        elif isinstance(event, str):
            text_parts.append(event)

    response: dict[str, Any] = {"events": events}
    if text_parts:
        response["output_text"] = "\n".join(dict.fromkeys(text_parts))
    if response_id:
        response["id"] = response_id
    if trace_id:
        response["trace_id"] = trace_id
    return response


def extract_agent_app_ids_by_name(response_body: Any) -> dict[str, str]:
    versions = _agent_version_items(response_body)
    agent_ids: dict[str, str] = {}
    for version in versions:
        if not isinstance(version, dict):
            continue
        name = _nested_get(version, ("manifest", "name"))
        agent_app_id = _agent_app_id_from_version(version)
        if isinstance(name, str) and isinstance(agent_app_id, str) and agent_app_id:
            agent_ids[name] = agent_app_id
    return agent_ids


def _agent_version_items(response_body: Any) -> list[Any]:
    if isinstance(response_body, list):
        return response_body
    if not isinstance(response_body, dict):
        return []
    candidates = [
        response_body.get("items"),
        response_body.get("data"),
        _nested_get(response_body, ("data", "items")),
        _nested_get(response_body, ("result", "items")),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
    return []


def _agent_app_id_from_version(version: dict[str, Any]) -> str | None:
    candidates = [
        version.get("agent_app_id"),
        version.get("agentAppId"),
        version.get("agent_application_id"),
        version.get("agentApplicationId"),
        version.get("application_id"),
        version.get("applicationId"),
        _nested_get(version, ("agent_app", "id")),
        _nested_get(version, ("agentApp", "id")),
        _nested_get(version, ("application", "id")),
        _nested_get(version, ("manifest", "agent_app_id")),
        _nested_get(version, ("manifest", "agentAppId")),
    ]
    return next((value for value in candidates if isinstance(value, str) and value), None)


def _header_value(headers: dict[str, str], header_name: str) -> str:
    for key, value in headers.items():
        if key.lower() == header_name:
            return value.lower()
    return ""


def _looks_like_sse(raw_body: str) -> bool:
    return any(line.startswith("data:") for line in raw_body.splitlines())


def _event_string(event: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    return next((event.get(key) for key in keys if isinstance(event.get(key), str)), None)


def _decode_feedback_candidate(candidate: str) -> list[str]:
    decoded = [candidate]
    padded = candidate + "=" * (-len(candidate) % 4)
    for decoder in (base64.urlsafe_b64decode, base64.b64decode):
        try:
            decoded_bytes = decoder(padded.encode("utf-8"))
        except (ValueError, binascii.Error):
            continue
        try:
            decoded.append(decoded_bytes.decode("utf-8"))
        except UnicodeDecodeError:
            continue
    return decoded


def _find_nested_string(source: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(source, dict):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value:
                return value
        for value in source.values():
            found = _find_nested_string(value, keys)
            if found:
                return found
    if isinstance(source, list):
        for item in source:
            found = _find_nested_string(item, keys)
            if found:
                return found
    return None
