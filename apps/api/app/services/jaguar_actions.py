import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings, settings
from app.models.incident import Approval


class JaguarActionError(RuntimeError):
    pass


@dataclass(frozen=True)
class PreparedJaguarAction:
    action_id: str
    action_type: str
    title: str
    risk: str | None = None
    external_status: str | None = None


ACTION_REQUEST_PATTERN = re.compile(
    r"DRAFTED\s+(?P<title>[A-Z][A-Z ]{2,80})"
    r"\s*\((?P<body>[^)]*?\baction_request\s+(?P<id>[a-zA-Z0-9_-]{16,})[^)]*)\)",
    re.IGNORECASE,
)
ACTION_TABLE_PATTERN = re.compile(
    r"^\s*\|(?P<title_cell>[^|\n]*(?:restart|rollback)[^|\n]*)"
    r"\|\s*`?(?P<id>[a-zA-Z0-9_-]{16,})`?\s*"
    r"\|(?P<status_cell>[^|\n]*(?:approval|proposed)[^|\n]*)"
    r"\|(?P<risk_cell>[^|\n]*)\|?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def parse_prepared_jaguar_actions(text: str | None) -> list[PreparedJaguarAction]:
    if not text:
        return []

    actions: list[PreparedJaguarAction] = []
    seen_ids: set[str] = set()
    normalized = text.replace("\r\n", "\n")

    for action in _parse_drafted_actions(normalized):
        if action.action_id not in seen_ids:
            actions.append(action)
            seen_ids.add(action.action_id)

    for action in _parse_action_table_rows(normalized):
        if action.action_id not in seen_ids:
            actions.append(action)
            seen_ids.add(action.action_id)

    return actions


def sync_jaguar_approvals_from_recommendation(
    incident_id: str, existing_approvals: list[Approval], recommendation: str | None
) -> list[Approval]:
    existing_external_ids = {
        approval.external_action_id
        for approval in existing_approvals
        if approval.external_system == "jaguar" and approval.external_action_id
    }
    approvals: list[Approval] = []
    for action in parse_prepared_jaguar_actions(recommendation):
        if action.action_id in existing_external_ids:
            continue
        approvals.append(
            Approval(
                incident_id=incident_id,
                action_type=f"jaguar:{action.action_type}",
                external_system="jaguar",
                external_action_id=action.action_id,
                external_status=action.external_status or "proposed",
                risk=action.risk,
                title=action.title,
                details={
                    "source": "jaguar_mcp",
                    "approval_tool": _approval_tool(action.action_type),
                },
            )
        )
        existing_external_ids.add(action.action_id)
    return approvals


def sync_jaguar_approvals_from_texts(
    incident_id: str, existing_approvals: list[Approval], texts: list[str | None]
) -> list[Approval]:
    return sync_jaguar_approvals_from_recommendation(
        incident_id,
        existing_approvals,
        "\n\n".join(text for text in texts if text),
    )


def reconcile_jaguar_approvals_from_texts(
    incident_id: str, existing_approvals: list[Approval], texts: list[str | None]
) -> list[Approval]:
    """Sync trace-derived Jaguar actions and prune stale pending parser artifacts."""
    recommendation = "\n\n".join(text for text in texts if text)
    valid_actions = parse_prepared_jaguar_actions(recommendation)
    valid_ids = {action.action_id for action in valid_actions}
    retained_ids: set[str] = set()
    retained_approvals: list[Approval] = []

    for approval in existing_approvals:
        if (
            approval.external_system == "jaguar"
            and approval.status == "pending"
            and approval.details.get("source") == "jaguar_mcp"
        ):
            if approval.external_action_id not in valid_ids:
                continue
            if approval.external_action_id in retained_ids:
                continue
            retained_ids.add(approval.external_action_id or "")
        retained_approvals.append(approval)

    existing_approvals[:] = retained_approvals
    return sync_jaguar_approvals_from_recommendation(
        incident_id, existing_approvals, recommendation
    )


def extract_action_texts_from_spans(spans: list[dict[str, Any]]) -> list[str]:
    texts: list[str] = []
    for span in spans:
        texts.extend(_extract_text_candidates(span))
    return texts


class JaguarActionClient:
    def __init__(self, integration_settings: Settings = settings) -> None:
        self.settings = integration_settings

    def is_configured(self) -> bool:
        return bool(
            self.settings.jaguar_mcp_url
            and self.settings.jaguar_mcp_api_key
            and self.settings.jaguar_operator_secret
        )

    def resolve_approval(self, approval: Approval, approved: bool, note: str | None) -> str:
        if approval.external_system != "jaguar" or approval.external_action_id is None:
            return "No external Jaguar action attached."
        if not self.is_configured():
            raise JaguarActionError(
                "Jaguar approval bridge is not configured. Set HALO_JAGUAR_MCP_API_KEY "
                "and HALO_JAGUAR_OPERATOR_SECRET."
            )

        tool_name = _approval_tool(approval.action_type)
        arguments: dict[str, Any] = {"id": approval.external_action_id}
        if approved:
            arguments["note"] = note or "approved from Halo"
        else:
            tool_name = "reject_action"
            arguments["reason"] = note or "rejected from Halo"

        body = {
            "jsonrpc": "2.0",
            "id": f"halo-{approval.id}",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.jaguar_mcp_api_key}",
            "X-Operator-Secret": self.settings.jaguar_operator_secret or "",
            "Content-Type": "application/json",
            "User-Agent": "Halo/0.1 JaguarApprovalBridge",
        }
        request = Request(
            self.settings.jaguar_mcp_url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(
                request, timeout=self.settings.jaguar_action_timeout_seconds
            ) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise JaguarActionError(
                f"Jaguar MCP approval request failed with HTTP {exc.code}"
            ) from exc
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise JaguarActionError(
                f"Jaguar MCP approval request failed: {exc.__class__.__name__}"
            ) from exc

        if payload.get("error"):
            raise JaguarActionError(
                f"Jaguar MCP approval error: {payload['error'].get('message', 'unknown error')}"
            )

        result = payload.get("result") or {}
        if result.get("isError"):
            raise JaguarActionError(_content_text(result) or "Jaguar rejected the approval action.")
        return _content_text(result) or "Jaguar action resolved."


def get_jaguar_action_client() -> JaguarActionClient:
    return JaguarActionClient()


def _approval_tool(action_type: str) -> str:
    return "approve_action"


def _parse_drafted_actions(text: str) -> list[PreparedJaguarAction]:
    actions: list[PreparedJaguarAction] = []
    for match in ACTION_REQUEST_PATTERN.finditer(text):
        context = text[max(0, match.start() - 80) : min(len(text), match.end() + 120)]
        inferred = _infer_action_type(context, match.group("title"))
        if inferred is None:
            continue
        action_type, title = inferred
        body = match.group("body")
        actions.append(
            PreparedJaguarAction(
                action_id=match.group("id"),
                action_type=action_type,
                title=title,
                risk=_clean_risk(_extract_risk(body) or _extract_risk(context)),
                external_status=_extract_status(body) or _extract_status(context),
            )
        )
    return actions


def _parse_action_table_rows(text: str) -> list[PreparedJaguarAction]:
    actions: list[PreparedJaguarAction] = []
    for line in text.splitlines():
        match = ACTION_TABLE_PATTERN.match(line)
        if not match:
            continue
        context = line
        inferred = _infer_action_type(context, match.group("title_cell"))
        if inferred is None:
            continue
        action_type, title = inferred
        actions.append(
            PreparedJaguarAction(
                action_id=match.group("id"),
                action_type=action_type,
                title=title,
                risk=_clean_risk(_extract_risk(match.group("risk_cell"))),
                external_status=_extract_status(match.group("status_cell")),
            )
        )
    return actions


def _infer_action_type(context: str, title_label: str | None) -> tuple[str, str] | None:
    source = " ".join(part for part in (context, title_label) if part).lower()
    if not re.search(r"\b(action_request|approval|proposed)\b", source):
        return None
    if "rollback" in source:
        return "rollback", "Rollback"
    if "restart" in source:
        return "worker_restart", "Worker Restart"
    return None


def _clean_risk(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().strip("|").strip().capitalize()


def _extract_risk(context: str) -> str | None:
    match = re.search(r"\b(low|medium|high|critical)\b", context, re.IGNORECASE)
    return match.group(1) if match else None


def _extract_status(context: str) -> str | None:
    if re.search(r"awaiting operator approval|status:\s*proposed", context, re.IGNORECASE):
        return "proposed"
    if re.search(r"\bapproved\b", context, re.IGNORECASE):
        return "approved"
    if re.search(r"\brejected\b", context, re.IGNORECASE):
        return "rejected"
    return None


def _content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    parts = [item.get("text", "") for item in content if isinstance(item, dict)]
    return "\n".join(part for part in parts if part)


def _extract_text_candidates(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
        stripped = value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                candidates.extend(_extract_text_candidates(json.loads(stripped)))
            except json.JSONDecodeError:
                pass
        return candidates
    if isinstance(value, dict):
        texts: list[str] = []
        for nested in value.values():
            texts.extend(_extract_text_candidates(nested))
        return texts
    if isinstance(value, list):
        texts: list[str] = []
        for nested in value:
            texts.extend(_extract_text_candidates(nested))
        return texts
    return []
