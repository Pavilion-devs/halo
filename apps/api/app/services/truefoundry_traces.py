import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings, settings
from app.models.incident import Incident, TraceLink, utc_now
from app.schemas.traces import IncidentTracesResponse, TraceSummary


@dataclass
class TraceLookupResult:
    trace_id: str
    summary: dict[str, Any]


@dataclass
class TraceQueryWindow:
    start_time: datetime
    end_time: datetime


class TraceLookupError(RuntimeError):
    pass


class TrueFoundryTraceService:
    def __init__(self, integration_settings: Settings = settings) -> None:
        self.settings = integration_settings

    def should_lookup(self) -> bool:
        return bool(
            self.settings.truefoundry_traces_enabled
            and self.base_url
            and self.settings.truefoundry_virtual_account_token
        )

    @property
    def base_url(self) -> str | None:
        return self.settings.truefoundry_traces_base_url or self.settings.truefoundry_base_url

    def summarize_incident_traces(self, incident: Incident) -> IncidentTracesResponse:
        # Trace links that carry a cached summary snapshot are served directly,
        # without a live span-store call. This keeps demo-critical traces fast and
        # deterministic even when the live spans API is slow or unavailable.
        live_links = [
            trace_link
            for trace_link in incident.trace_links
            if cached_trace_summary(trace_link) is None
        ]

        lookups: dict[str, TraceLookupResult] = {}
        lookup_error: str | None = None
        if live_links and self.should_lookup():
            trace_ids = [trace_link.trace_id for trace_link in live_links]
            try:
                lookups = self.query_trace_summaries(trace_ids, live_links)
            except TraceLookupError as exc:
                lookup_error = str(exc)

        traces: list[TraceSummary] = []
        for trace_link in incident.trace_links:
            cached = cached_trace_summary(trace_link)
            if cached is not None:
                traces.append(
                    trace_summary_from_link(
                        trace_link, lookup_status="found", live_summary=cached
                    )
                )
                continue
            if not self.should_lookup():
                traces.append(trace_summary_from_link(trace_link, lookup_status="disabled"))
                continue
            if lookup_error is not None:
                traces.append(
                    trace_summary_from_link(
                        trace_link, lookup_status="error", error=lookup_error
                    )
                )
                continue
            lookup = lookups.get(trace_link.trace_id)
            if lookup is None:
                traces.append(trace_summary_from_link(trace_link, lookup_status="not_found"))
                continue
            traces.append(
                trace_summary_from_link(
                    trace_link, lookup_status="found", live_summary=lookup.summary
                )
            )

        return IncidentTracesResponse(
            incident_id=incident.id, traces=traces, error=lookup_error
        )

    def query_trace_summaries(
        self, trace_ids: list[str], trace_links: list[TraceLink]
    ) -> dict[str, TraceLookupResult]:
        unique_trace_ids = sorted(set(trace_ids))
        if not unique_trace_ids:
            return {}

        spans = self.query_spans(unique_trace_ids, build_query_window(trace_links, self.settings))
        spans_by_trace_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for span in spans:
            trace_id = _span_value(span, "traceId", "trace_id")
            if isinstance(trace_id, str) and trace_id in unique_trace_ids:
                spans_by_trace_id[trace_id].append(span)

        return {
            trace_id: TraceLookupResult(trace_id=trace_id, summary=summarize_spans(spans))
            for trace_id, spans in spans_by_trace_id.items()
        }

    def query_spans(
        self, trace_ids: list[str], query_window: TraceQueryWindow
    ) -> list[dict[str, Any]]:
        base_url = self.base_url
        token = self.settings.truefoundry_virtual_account_token
        if not base_url or not token:
            raise TraceLookupError("TrueFoundry trace lookup is not configured")

        url = f"{base_url.rstrip('/')}/{self.settings.truefoundry_traces_query_path.lstrip('/')}"
        body = build_spans_query_payload(trace_ids, query_window, self.settings)
        spans: list[dict[str, Any]] = []
        page_token: str | None = None

        while True:
            request_body = dict(body)
            if page_token:
                request_body["pageToken"] = page_token
            response_body = self._post_spans_query(url, token, request_body)
            data = response_body.get("data", [])
            if not isinstance(data, list):
                raise TraceLookupError("TrueFoundry spans query returned invalid data")
            spans.extend([span for span in data if isinstance(span, dict)])

            pagination = response_body.get("pagination")
            page_token = pagination.get("nextPageToken") if isinstance(pagination, dict) else None
            if not page_token:
                return spans

    def _post_spans_query(
        self, url: str, token: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        request = Request(
            url=url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": self.settings.truefoundry_user_agent,
            },
            method="POST",
        )
        try:
            with urlopen(  # noqa: S310 - URL is operator-configured service endpoint.
                request,
                timeout=self.settings.truefoundry_traces_timeout_seconds,
            ) as response:
                raw_body = response.read().decode("utf-8")
                response_body = json.loads(raw_body) if raw_body else {}
                if not isinstance(response_body, dict):
                    raise TraceLookupError("TrueFoundry spans query returned a non-object")
                return response_body
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise TraceLookupError(f"HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise TraceLookupError(str(exc.reason)) from exc
        except TimeoutError as exc:
            raise TraceLookupError("lookup timed out") from exc
        except json.JSONDecodeError as exc:
            raise TraceLookupError("lookup returned invalid JSON") from exc


def get_trace_service() -> TrueFoundryTraceService:
    return TrueFoundryTraceService()


def build_query_window(
    trace_links: list[TraceLink],
    integration_settings: Settings = settings,
    now: datetime | None = None,
) -> TraceQueryWindow:
    current_time = now or utc_now()
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=UTC)
    lookback_start = current_time - timedelta(
        hours=integration_settings.truefoundry_traces_lookback_hours
    )
    earliest_trace_time = min((trace.created_at for trace in trace_links), default=current_time)
    if earliest_trace_time.tzinfo is None:
        earliest_trace_time = earliest_trace_time.replace(tzinfo=UTC)
    trace_start = earliest_trace_time - timedelta(minutes=5)
    return TraceQueryWindow(
        start_time=min(lookback_start, trace_start),
        end_time=current_time + timedelta(minutes=5),
    )


def build_spans_query_payload(
    trace_ids: list[str],
    query_window: TraceQueryWindow,
    integration_settings: Settings = settings,
) -> dict[str, Any]:
    return {
        "dataRoutingDestination": integration_settings.truefoundry_traces_data_routing_destination,
        "endTime": _format_tfy_time(query_window.end_time),
        "includeFeedbacks": False,
        "limit": 200,
        "sortDirection": "desc",
        "startTime": _format_tfy_time(query_window.start_time),
        "traceIds": sorted(set(trace_ids)),
    }


def cached_trace_summary(trace_link: TraceLink) -> dict[str, Any] | None:
    """Return a stored trace summary snapshot if present on the trace link.

    Demo-critical traces carry a ``cached_summary`` in their metadata so the trace
    evidence panel renders deterministically without depending on the live span
    store, which can be slow or temporarily unavailable.
    """
    metadata = trace_link.metadata if isinstance(trace_link.metadata, dict) else {}
    cached = metadata.get("cached_summary")
    return cached if isinstance(cached, dict) else None


def trace_summary_from_link(
    trace_link: TraceLink,
    lookup_status: str,
    live_summary: dict[str, Any] | None = None,
    error: str | None = None,
) -> TraceSummary:
    return TraceSummary(
        internal_id=trace_link.id,
        trace_id=trace_link.trace_id,
        created_at=trace_link.created_at,
        metadata=trace_link.metadata,
        provisional=is_provisional_trace(trace_link),
        lookup_status=lookup_status,
        live_summary=live_summary,
        error=error,
    )


def is_provisional_trace(trace_link: TraceLink) -> bool:
    return bool(trace_link.metadata.get("provisional", False))


def summarize_spans(spans: list[dict[str, Any]]) -> dict[str, Any]:
    root_span = find_root_span(spans)
    all_attributes = [span_attributes(span) for span in spans]
    model_span = first_span_by_type(spans, "Model")
    mcp_spans = [
        span
        for span in spans
        if any(key.startswith("tfy.mcp.") for key in span_attributes(span))
        or "mcp" in str(_span_value(span, "spanName", "span_name")).lower()
    ]

    return {
        "root_span_name": _span_value(root_span, "spanName", "span_name") if root_span else None,
        "span_count": len(spans),
        "status": summarize_status(spans),
        "model_name": model_name_from_span(model_span, all_attributes),
        "latency_ms": latency_ms_from_spans(spans, model_span),
        "guardrails_triggered": guardrails_from_attributes(all_attributes),
        "mcp_tool_spans": mcp_tool_summaries(mcp_spans),
        "raw_span_sample": spans[:5],
    }


def find_root_span(spans: list[dict[str, Any]]) -> dict[str, Any] | None:
    for span in spans:
        parent_span_id = _span_value(span, "parentSpanId", "parent_span_id")
        if parent_span_id in ("", None):
            return span
    return spans[0] if spans else None


def summarize_status(spans: list[dict[str, Any]]) -> str | None:
    statuses = [
        status
        for status in (_span_value(span, "statusCode", "status_code") for span in spans)
        if isinstance(status, str)
    ]
    if any(status.lower() in {"error", "status_code_error"} for status in statuses):
        return "error"
    if any(status.lower() == "ok" for status in statuses):
        return "ok"
    return statuses[0] if statuses else None


def model_name_from_span(
    model_span: dict[str, Any] | None, all_attributes: list[dict[str, Any]]
) -> str | None:
    candidates: list[Any] = []
    if model_span:
        candidates.append(span_attributes(model_span).get("tfy.model.name"))
        candidates.append(_span_value(model_span, "spanName", "span_name"))
    for attributes in all_attributes:
        candidates.append(attributes.get("tfy.model.name"))
    return next((value for value in candidates if isinstance(value, str) and value), None)


def latency_ms_from_spans(
    spans: list[dict[str, Any]], model_span: dict[str, Any] | None
) -> int | float | None:
    if model_span:
        model_latency = span_attributes(model_span).get("tfy.model.metric.latency_in_ms")
        if isinstance(model_latency, int | float):
            return model_latency
    root_span = find_root_span(spans)
    duration_ns = _span_value(root_span, "durationNs", "duration_ns") if root_span else None
    if isinstance(duration_ns, int | float):
        return round(duration_ns / 1_000_000, 2)
    return None


def guardrails_from_attributes(all_attributes: list[dict[str, Any]]) -> list[str]:
    guardrails: list[str] = []
    for attributes in all_attributes:
        values = [
            attributes.get("tfy.triggered_guardrail_fqns"),
            attributes.get("tfy.guardrail.fqn"),
            attributes.get("tfy.guardrail.name"),
        ]
        for value in values:
            if isinstance(value, str):
                guardrails.append(value)
            elif isinstance(value, list):
                guardrails.extend([item for item in value if isinstance(item, str)])
    return sorted(set(guardrails))


def mcp_tool_summaries(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for span in spans:
        attributes = span_attributes(span)
        summaries.append(
            {
                "span_name": _span_value(span, "spanName", "span_name"),
                "status": _span_value(span, "statusCode", "status_code"),
                "server": attributes.get("tfy.mcp.server.name")
                or attributes.get("tfy.mcp_server.name"),
                "tool": attributes.get("tfy.mcp.tool.name") or attributes.get("tfy.mcp_tool.name"),
            }
        )
    return summaries


def first_span_by_type(spans: list[dict[str, Any]], span_type: str) -> dict[str, Any] | None:
    return next(
        (span for span in spans if span_attributes(span).get("tfy.span_type") == span_type),
        None,
    )


def spans_by_type(spans: list[dict[str, Any]], span_type: str) -> list[dict[str, Any]]:
    return [span for span in spans if span_attributes(span).get("tfy.span_type") == span_type]


def span_attributes(span: dict[str, Any]) -> dict[str, Any]:
    attributes = _span_value(span, "spanAttributes", "span_attributes")
    return attributes if isinstance(attributes, dict) else {}


def _span_value(span: dict[str, Any] | None, *keys: str) -> Any:
    if not isinstance(span, dict):
        return None
    for key in keys:
        if key in span:
            return span[key]
    return None


def _format_tfy_time(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
