#!/usr/bin/env python3

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import Session

from app.db.session import engine
from app.models.incident import (
    Approval,
    ApprovalStatus,
    Incident,
    IncidentCheckpoint,
    IncidentEvent,
    IncidentMode,
    IncidentSeverity,
    IncidentStage,
    IncidentStatus,
    TraceLink,
    utc_now,
)
from app.repositories.incidents import IncidentRepository

SOURCE_INCIDENT_ID = "inc_ae2a13368c47"

# Real trace summary captured from the live Jaguar proof run (trace
# 019e97822312766daef28a9823b35178). Stored as a snapshot so the War Room trace
# evidence panel renders deterministically without depending on the live span
# store, which is slow/unreliable for older traces. Shape matches summarize_spans().
DEMO_TRACE_SUMMARY: dict = {
    "root_span_name": "AgentResponse: halo/halo-vm-normal",
    "span_count": 175,
    "status": "ok",
    "model_name": "aws-bedrock/us.anthropic.claude-opus-4-6-v1",
    "latency_ms": None,
    "guardrails_triggered": [
        "halo-guardrails/secrets-detection",
        "halo:guardrail-config-group:halo-guardrails:guardrail-config:secrets-detection",
    ],
    "mcp_tool_spans": [
        {"span_name": "MCP: tools/call: get_worker_status", "status": "Ok", "server": "jaguar-observe", "tool": "get_worker_status"},
        {"span_name": "MCP: tools/call: get_ingestion_diagnostics", "status": "Ok", "server": "jaguar-observe", "tool": "get_ingestion_diagnostics"},
        {"span_name": "MCP: tools/call: get_recent_deploys", "status": "Ok", "server": "jaguar-observe", "tool": "get_recent_deploys"},
        {"span_name": "MCP: tools/call: get_recent_failures", "status": "Ok", "server": "jaguar-observe", "tool": "get_recent_failures"},
        {"span_name": "MCP: tools/call: get_recent_status_events", "status": "Ok", "server": "jaguar-observe", "tool": "get_recent_status_events"},
        {"span_name": "MCP: tools/call: get_runbook", "status": "Ok", "server": "jaguar-observe", "tool": "get_runbook"},
        {"span_name": "MCP: tools/call: prepare_worker_restart", "status": "Ok", "server": "jaguar-act", "tool": "prepare_worker_restart"},
        {"span_name": "MCP: tools/call: draft_incident_update", "status": "Ok", "server": "jaguar-act", "tool": "draft_incident_update"},
    ],
}


def build_demo_recommendation(action_id: str) -> str:
    return "\n".join(
        [
            "## Incident Summary",
            "",
            "**Classification:** SEV-1 CRITICAL — Jaguar data blackout",
            "",
            "| Signal | Current state |",
            "| --- | --- |",
            "| **Worker process** | Restart executed successfully; heartbeat is fresh again. |",
            "| **Ingestion** | Still degraded — all live streams remain dead. |",
            "| **Root cause** | GoldRush invalidated the stream token and reconnect reused stale auth. |",
            "| **Impact** | New Solana launches, price updates, and candles are stale or missing. |",
            "",
            "## Evidence",
            "",
            "- GoldRush returned `AUTHENTICATION_ERROR / INVALID_TOKEN` across all four subscriptions.",
            "- Stream diagnostics still show `events: 0` after the restart.",
            "- Jaguar critical alerts accumulated because scoring kept running on stale data.",
            "",
            "## Recovery Action Executed",
            "",
            f"| Action | ID | Status | Risk |",
            "| --- | --- | --- | --- |",
            f"| **Worker Restart** | `{action_id}` | Approved in Halo and executed by Jaguar ops-runner | Medium |",
            "",
            "What happened:",
            "- Halo investigated Jaguar through TrueFoundry MCP tools.",
            "- Halo drafted the risky restart behind a human approval gate.",
            "- Approval passed through Halo to Jaguar, then Jaguar ops-runner executed the restart.",
            "",
            "## Verification After Action",
            "",
            "- `get_worker_status`: process recovered and heartbeat is healthy again.",
            "- `get_ingestion_diagnostics`: live stream counters still are not incrementing.",
            "- Conclusion: container uptime was only the symptom; the remaining problem is upstream credential invalidation.",
            "",
            "## Escalation Path",
            "",
            "- Rotate or repair the GoldRush credential in Jaguar's secrets path.",
            "- Re-run ingestion verification until stream events resume and candle lag collapses.",
            "- Only then close the incident.",
        ]
    )


def main() -> int:
    now = utc_now()

    with Session(engine) as session:
        repo = IncidentRepository(session)
        source = repo.get(SOURCE_INCIDENT_ID)
        if source is None:
            raise SystemExit(f"source incident not found: {SOURCE_INCIDENT_ID}")

        approved = next(
            (
                approval
                for approval in source.approvals
                if approval.external_system == "jaguar"
                and approval.external_action_id
                and approval.status == ApprovalStatus.APPROVED
            ),
            None,
        )
        if approved is None:
            raise SystemExit("source incident does not contain an approved Jaguar action")

        if not source.trace_links:
            raise SystemExit("source incident does not contain a trace link")

        trace = source.trace_links[0]
        recommendation = build_demo_recommendation(approved.external_action_id or approved.id)

        incident = Incident(
            title="Jaguar worker offline after recent deploy - clean demo proof",
            severity=IncidentSeverity(source.severity),
            status=IncidentStatus.RUNNING,
            environment=source.environment,
            product=source.product,
            mode=IncidentMode.NORMAL,
            stage=IncidentStage.MONITOR,
            summary=(
                "Halo approved and Jaguar executed the worker restart, but live ingestion is still "
                "degraded because GoldRush continues rejecting the streaming credential."
            ),
            latest_recommendation=recommendation,
            current_agent="halo-normal",
            current_virtual_model="halo-vm-normal",
            last_failure=None,
            fallback_action=(
                "Escalate to GoldRush credential rotation and Jaguar secrets-store validation."
            ),
            created_at=now,
            updated_at=now,
        )

        approval = Approval(
            incident_id=incident.id,
            action_type=approved.action_type,
            status=ApprovalStatus.APPROVED,
            external_system=approved.external_system,
            external_action_id=approved.external_action_id,
            external_status="executed",
            risk=approved.risk,
            title=approved.title,
            details={
                **approved.details,
                "external_response": (
                    f"APPROVED action_request {approved.external_action_id} — Jaguar accepted "
                    "the request and ops-runner executed the worker restart."
                ),
            },
            requested_at=now + timedelta(seconds=4),
            resolved_at=now + timedelta(seconds=5),
        )

        incident.events = [
            IncidentEvent(
                incident_id=incident.id,
                type="incident.created",
                payload={
                    "title": incident.title,
                    "severity": incident.severity,
                    "mode": incident.mode,
                },
                created_at=now,
            ),
            IncidentEvent(
                incident_id=incident.id,
                type="workflow.stage_completed",
                payload={
                    "stage": IncidentStage.CLASSIFY,
                    "mode": IncidentMode.NORMAL,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now + timedelta(seconds=1),
            ),
            IncidentEvent(
                incident_id=incident.id,
                type="truefoundry.invocation_succeeded",
                payload={
                    "agent_name": "halo-normal",
                    "recommendation_updated": True,
                    "stage": IncidentStage.CLASSIFY,
                    "trace_id": trace.trace_id,
                },
                created_at=now + timedelta(seconds=2),
            ),
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
                    "source": "live_demo_seed",
                },
                created_at=now + timedelta(seconds=4),
            ),
            IncidentEvent(
                incident_id=incident.id,
                type="approval.resolved",
                payload={
                    "approval_id": approval.id,
                    "approved": True,
                    "note": "seeded from live Jaguar approval proof",
                    "external_system": approval.external_system,
                    "external_action_id": approval.external_action_id,
                    "external_status": approval.external_status,
                },
                created_at=now + timedelta(seconds=5),
            ),
            IncidentEvent(
                incident_id=incident.id,
                type="external.action_executed",
                payload={
                    "action_type": approval.action_type,
                    "external_system": approval.external_system,
                    "external_action_id": approval.external_action_id,
                    "result": "worker restart executed by Jaguar ops-runner",
                },
                created_at=now + timedelta(seconds=6),
            ),
            IncidentEvent(
                incident_id=incident.id,
                type="verification.completed",
                payload={
                    "outcome": "degraded",
                    "result": (
                        "worker heartbeat recovered, but GoldRush INVALID_TOKEN persists and "
                        "all streams remain dead"
                    ),
                },
                created_at=now + timedelta(seconds=7),
            ),
        ]

        incident.checkpoints = [
            IncidentCheckpoint(
                incident_id=incident.id,
                stage=IncidentStage.INTAKE,
                state={
                    "reason": "seeded from live Jaguar incident proof",
                    "mode": IncidentMode.NORMAL,
                    "status": IncidentStatus.OPEN,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now,
            ),
            IncidentCheckpoint(
                incident_id=incident.id,
                stage=IncidentStage.CLASSIFY,
                state={
                    "reason": "completed classify from live Jaguar evidence",
                    "mode": IncidentMode.NORMAL,
                    "status": IncidentStatus.RUNNING,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now + timedelta(seconds=2),
            ),
            IncidentCheckpoint(
                incident_id=incident.id,
                stage=IncidentStage.MONITOR,
                state={
                    "reason": "action executed; monitoring recovery and root cause",
                    "mode": IncidentMode.NORMAL,
                    "status": IncidentStatus.RUNNING,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now + timedelta(seconds=7),
            ),
        ]

        incident.approvals = [approval]
        incident.trace_links = [
            TraceLink(
                incident_id=incident.id,
                trace_id=trace.trace_id,
                metadata={**trace.metadata, "cached_summary": DEMO_TRACE_SUMMARY},
                created_at=trace.created_at,
            )
        ]
        incident.checkpoint_index = len(incident.checkpoints)

        repo.create(incident)
        print(incident.id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
