from datetime import UTC

from app.models.incident import (
    Approval,
    ApprovalStatus,
    Incident,
    IncidentCheckpoint,
    IncidentEvent,
    IncidentMode,
    IncidentStage,
    IncidentStatus,
    TraceLink,
    utc_now,
)
from app.schemas.incident import IncidentApproveRequest, IncidentRunRequest
from app.services.jaguar_actions import (
    JaguarActionClient,
    JaguarActionError,
    parse_prepared_jaguar_actions,
    reconcile_jaguar_approvals_from_texts,
    sync_jaguar_approvals_from_recommendation,
    sync_jaguar_approvals_from_texts,
)
from app.services.truefoundry import (
    TrueFoundryAgentService,
    TrueFoundryInvocationError,
    trace_link_from_failure,
    trace_link_from_result,
)

STAGE_SEQUENCE = [
    IncidentStage.INTAKE,
    IncidentStage.CLASSIFY,
    IncidentStage.GATHER_EVIDENCE,
    IncidentStage.DRAFT_PLAN,
    IncidentStage.EXECUTE_SAFE_ACTIONS,
    IncidentStage.REQUEST_APPROVAL,
    IncidentStage.MONITOR,
    IncidentStage.HANDOFF_OR_CLOSE,
]


def seed_incident(incident: Incident) -> Incident:
    incident.events.append(
        IncidentEvent(
            incident_id=incident.id,
            type="incident.created",
            payload={
                "title": incident.title,
                "severity": incident.severity,
                "mode": incident.mode,
            },
        )
    )
    return persist_checkpoint(incident, "incident accepted into Halo workflow")


def run_next_step(
    incident: Incident,
    request: IncidentRunRequest,
    agent_service: TrueFoundryAgentService | None = None,
) -> Incident:
    if request.force_mode is not None:
        set_mode(incident, request.force_mode, "operator requested mode override")

    incident.status = IncidentStatus.RUNNING
    next_stage = _next_stage(incident.stage)
    incident.stage = next_stage

    if next_stage == IncidentStage.REQUEST_APPROVAL:
        incident.status = IncidentStatus.WAITING_FOR_APPROVAL
        approval = Approval(
            incident_id=incident.id,
            action_type="post_internal_status_update",
        )
        incident.approvals.append(approval)
        incident.latest_recommendation = (
            "Approve the drafted internal update before action tools run."
        )
        incident.events.append(
            IncidentEvent(
                incident_id=incident.id,
                type="approval.requested",
                payload={"approval_id": approval.id, "action_type": approval.action_type},
            )
        )
    elif next_stage == IncidentStage.HANDOFF_OR_CLOSE:
        incident.status = IncidentStatus.HANDED_OFF
        incident.latest_recommendation = "Generate a human handoff packet with current evidence."
    else:
        incident.latest_recommendation = _recommendation_for_stage(next_stage)

    if request.scenario and not _truefoundry_enabled(agent_service):
        incident.trace_links.append(
            TraceLink(
                incident_id=incident.id,
                trace_id=f"pending-{incident.id}-{incident.checkpoint_index + 1}",
                metadata={
                    "scenario": request.scenario,
                    "demo_run": str(request.demo_run).lower(),
                    "mode": incident.mode,
                    "stage": next_stage,
                },
            )
        )

    incident.events.append(
        IncidentEvent(
            incident_id=incident.id,
            type="workflow.stage_completed",
            payload={
                "stage": next_stage,
                "mode": incident.mode,
                "agent": incident.current_agent,
                "virtual_model": incident.current_virtual_model,
            },
        )
    )
    persist_checkpoint(incident, f"completed {next_stage}")
    if _truefoundry_enabled(agent_service):
        invoke_truefoundry_agent(incident, request, agent_service)
    return incident


def invoke_truefoundry_agent(
    incident: Incident,
    request: IncidentRunRequest,
    agent_service: TrueFoundryAgentService,
) -> Incident:
    try:
        result = agent_service.invoke(incident, request)
    except TrueFoundryInvocationError as exc:
        trace_link = trace_link_from_failure(incident, request, exc)
        if trace_link is not None:
            incident.trace_links.append(trace_link)
        incident.last_failure = str(exc)
        incident.events.append(
            IncidentEvent(
                incident_id=incident.id,
                type="truefoundry.invocation_failed",
                payload={
                    "error": str(exc),
                    "mode": incident.mode,
                    "stage": incident.stage,
                    "trace_id": trace_link.trace_id if trace_link else None,
                },
            )
        )
        if incident.mode == IncidentMode.NORMAL:
            set_mode(incident, IncidentMode.DEGRADED, "TrueFoundry invocation failed")
        persist_checkpoint(incident, "truefoundry invocation failed")
        return incident

    if result is None:
        return incident

    if result.recommendation:
        incident.latest_recommendation = result.recommendation
        _sync_external_approvals(incident, result.recommendation)

    trace_link = trace_link_from_result(incident, request, result)
    if trace_link is not None:
        incident.trace_links.append(trace_link)

    incident.events.append(
        IncidentEvent(
            incident_id=incident.id,
            type="truefoundry.invocation_succeeded",
            payload={
                "agent_name": result.agent_name,
                "recommendation_updated": bool(result.recommendation),
                "stage": incident.stage,
                "trace_id": trace_link.trace_id if trace_link else None,
            },
        )
    )
    incident.updated_at = utc_now().astimezone(UTC)
    return incident


def resolve_approval(
    incident: Incident,
    request: IncidentApproveRequest,
    jaguar_action_client: JaguarActionClient | None = None,
) -> tuple[Incident, Approval | None]:
    approval = _find_approval(incident, request.approval_id)
    if approval is None:
        incident.events.append(
            IncidentEvent(
                incident_id=incident.id,
                type="approval.not_found",
                payload={"approval_id": request.approval_id},
            )
        )
        return incident, None

    if approval.external_system == "jaguar":
        client = jaguar_action_client or JaguarActionClient()
        try:
            external_response = client.resolve_approval(approval, request.approved, request.note)
        except JaguarActionError as exc:
            incident.last_failure = str(exc)
            incident.latest_recommendation = (
                "Halo has a pending Jaguar action, but external approval failed. "
                "Fix the Jaguar approval bridge configuration or approve in Jaguar /ops."
            )
            incident.events.append(
                IncidentEvent(
                    incident_id=incident.id,
                    type="approval.external_resolution_failed",
                    payload={
                        "approval_id": approval.id,
                        "external_system": approval.external_system,
                        "external_action_id": approval.external_action_id,
                        "approved": request.approved,
                        "error": str(exc),
                    },
                )
            )
            persist_checkpoint(incident, "external approval resolution failed")
            return incident, approval
        approval.external_status = "approved" if request.approved else "rejected"
        approval.details = {
            **approval.details,
            "external_response": external_response,
        }

    approval.status = ApprovalStatus.APPROVED if request.approved else ApprovalStatus.REJECTED
    approval.resolved_at = utc_now()
    incident.status = IncidentStatus.RUNNING if request.approved else IncidentStatus.HANDED_OFF
    incident.latest_recommendation = _approval_resolution_recommendation(
        incident.latest_recommendation,
        approval,
        request.approved,
    )
    incident.events.append(
        IncidentEvent(
            incident_id=incident.id,
            type="approval.resolved",
            payload={
                "approval_id": approval.id,
                "approved": request.approved,
                "note": request.note,
                "external_system": approval.external_system,
                "external_action_id": approval.external_action_id,
                "external_status": approval.external_status,
            },
        )
    )
    persist_checkpoint(incident, "approval resolved")
    return incident, approval


def set_mode(incident: Incident, mode: IncidentMode, reason: str) -> None:
    incident.mode = mode
    if mode == IncidentMode.NORMAL:
        incident.current_agent = "halo-normal"
        incident.current_virtual_model = "halo-vm-normal"
    elif mode == IncidentMode.DEGRADED:
        incident.current_agent = "halo-degraded"
        incident.current_virtual_model = "halo-vm-degraded"
        incident.fallback_action = "reduced tool access and shorter agent loop"
    else:
        incident.current_agent = "halo-blackout"
        incident.current_virtual_model = "halo-vm-degraded"
        incident.fallback_action = "read-only handoff mode"

    incident.events.append(
        IncidentEvent(
            incident_id=incident.id,
            type="mode.changed",
            payload={"mode": mode, "reason": reason},
        )
    )


def persist_checkpoint(incident: Incident, reason: str) -> Incident:
    incident.checkpoint_index += 1
    incident.updated_at = utc_now().astimezone(UTC)
    incident.checkpoints.append(
        IncidentCheckpoint(
            incident_id=incident.id,
            stage=incident.stage,
            state={
                "reason": reason,
                "mode": incident.mode,
                "status": incident.status,
                "agent": incident.current_agent,
                "virtual_model": incident.current_virtual_model,
            },
        )
    )
    return incident


def _next_stage(current: IncidentStage) -> IncidentStage:
    current_index = STAGE_SEQUENCE.index(current)
    if current_index >= len(STAGE_SEQUENCE) - 1:
        return IncidentStage.HANDOFF_OR_CLOSE
    return STAGE_SEQUENCE[current_index + 1]


def _find_approval(incident: Incident, approval_id: str | None) -> Approval | None:
    pending = [item for item in incident.approvals if item.status == ApprovalStatus.PENDING]
    if approval_id is None:
        return pending[-1] if pending else None
    return next((item for item in incident.approvals if item.id == approval_id), None)


def _sync_external_approvals(incident: Incident, recommendation: str | None) -> None:
    approvals = sync_jaguar_approvals_from_recommendation(
        incident.id, incident.approvals, recommendation
    )
    _attach_external_approvals(incident, approvals)


def _approval_resolution_recommendation(
    existing: str | None, approval: Approval, approved: bool
) -> str:
    fallback = (
        "Approval accepted. Continue with the next safe workflow step."
        if approved
        else "Approval rejected. Prepare a human handoff before taking action."
    )
    if not existing:
        return fallback

    outcome = "approved" if approved else "rejected"
    action_name = approval.title or approval.action_type
    action_id = approval.external_action_id or approval.id
    lines = [
        existing.rstrip(),
        "",
        "---",
        "",
        "### Approval outcome",
        f"- **Action:** {action_name}",
        f"- **Action request:** `{action_id}`",
        f"- **Decision:** {outcome}",
    ]
    if approval.external_system:
        lines.append(f"- **External system:** {approval.external_system}")
    if approval.external_status:
        lines.append(f"- **External status:** {approval.external_status}")
    external_response = approval.details.get("external_response")
    if isinstance(external_response, str) and external_response:
        lines.append(f"- **Bridge response:** {external_response}")
    return "\n".join(lines)


def sync_external_approvals_from_texts(
    incident: Incident, texts: list[str | None], source: str
) -> list[Approval]:
    if source == "trace_or_recommendation":
        valid_jaguar_ids = {
            action.action_id
            for action in parse_prepared_jaguar_actions(
                "\n\n".join(text for text in texts if text)
            )
        }
        approvals = reconcile_jaguar_approvals_from_texts(
            incident.id, incident.approvals, texts
        )
        _prune_stale_jaguar_approval_events(incident, valid_jaguar_ids)
    else:
        approvals = sync_jaguar_approvals_from_texts(incident.id, incident.approvals, texts)
    _attach_external_approvals(incident, approvals, source=source)
    if approvals or incident.status == IncidentStatus.WAITING_FOR_APPROVAL:
        incident.updated_at = utc_now().astimezone(UTC)
    return approvals


def _prune_stale_jaguar_approval_events(
    incident: Incident, valid_external_action_ids: set[str]
) -> None:
    retained_events: list[IncidentEvent] = []
    retained_valid_event_ids: set[str] = set()
    for event in incident.events:
        if event.type != "approval.requested":
            retained_events.append(event)
            continue
        payload = event.payload
        if (
            payload.get("source") != "trace_or_recommendation"
            or payload.get("external_system") != "jaguar"
        ):
            retained_events.append(event)
            continue
        external_action_id = payload.get("external_action_id")
        if external_action_id not in valid_external_action_ids:
            continue
        if external_action_id in retained_valid_event_ids:
            continue
        retained_valid_event_ids.add(external_action_id)
        retained_events.append(event)
    incident.events = retained_events


def _attach_external_approvals(
    incident: Incident, approvals: list[Approval], source: str = "recommendation"
) -> None:
    if not approvals:
        return

    incident.approvals.extend(approvals)
    incident.status = IncidentStatus.WAITING_FOR_APPROVAL
    incident.updated_at = utc_now().astimezone(UTC)
    for approval in approvals:
        incident.events.append(
            IncidentEvent(
                incident_id=incident.id,
                type="approval.requested",
                payload={
                    "approval_id": approval.id,
                    "action_type": approval.action_type,
                    "external_system": approval.external_system,
                    "external_action_id": approval.external_action_id,
                    "risk": approval.risk,
                    "title": approval.title,
                    "source": source,
                },
            )
        )


def _recommendation_for_stage(stage: IncidentStage) -> str:
    recommendations = {
        IncidentStage.CLASSIFY: "Classify severity using service impact and customer visibility.",
        IncidentStage.GATHER_EVIDENCE: (
            "Gather logs, recent deploys, alerts, and matching runbooks."
        ),
        IncidentStage.DRAFT_PLAN: (
            "Draft a reversible mitigation plan with explicit risk boundaries."
        ),
        IncidentStage.EXECUTE_SAFE_ACTIONS: (
            "Execute only read-heavy or low-risk coordination actions."
        ),
        IncidentStage.MONITOR: (
            "Watch recovery signals and prepare fallback or handoff if confidence drops."
        ),
    }
    return recommendations.get(stage, "Continue the incident workflow from the latest checkpoint.")


def _truefoundry_enabled(agent_service: TrueFoundryAgentService | None) -> bool:
    return agent_service is not None and agent_service.should_invoke()
