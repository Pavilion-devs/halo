#!/usr/bin/env python3
"""Seed (or reset) a demo incident that is sitting at 'awaiting approval'.

The pending approval is demo-local (external_system='jaguar-demo', details.demo_local=True),
so clicking Approve in the War Room resolves locally and instantly — no live VPS call — and
reveals the full executed -> verified outcome. Re-run this script to reset it to pending.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
for path in (str(ROOT), str(SCRIPTS)):
    if path not in sys.path:
        sys.path.insert(0, path)

from sqlalchemy import delete
from sqlmodel import Session

from app.db.models import (
    ApprovalRecord,
    IncidentCheckpointRecord,
    IncidentEventRecord,
    IncidentRecord,
    TraceLinkRecord,
)
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
from seed_live_jaguar_demo_incident import DEMO_TRACE_SUMMARY, build_demo_recommendation

INCIDENT_ID = "inc_demo_approval"
ACTION_ID = "cmq0u17ba000004jme5kju2vd"
TRACE_ID = "019e97822312766daef28a9823b35178"

PRE_RECOMMENDATION = "\n".join(
    [
        "## Incident Summary",
        "",
        "**Classification:** SEV-1 CRITICAL — Jaguar data blackout",
        "",
        "| Signal | Current state |",
        "| --- | --- |",
        "| **Worker process** | Heartbeat went missing right after the latest deploy. |",
        "| **Ingestion** | All four live streams stalled — events have stopped flowing. |",
        "| **Working theory** | The worker died after the deploy; a restart should bring it back. |",
        "| **Impact** | New Solana launches, price updates, and candles are stale or missing. |",
        "",
        "## Evidence",
        "",
        "- Pulled live worker status, ingestion diagnostics, recent deploys, and recent failures through Jaguar MCP tools.",
        "- Lined the blackout up against the deploy timeline.",
        "- Matched an operational runbook for worker recovery.",
        "",
        "## Recommended Action — awaiting your approval",
        "",
        "| Action | Status | Risk |",
        "| --- | --- | --- |",
        "| **Worker Restart** | Prepared — waiting for operator approval | Medium |",
        "",
        "Halo has prepared a worker restart but will not touch production on its own. Approve to let",
        "Halo execute it through Jaguar's ops path; it will then verify whether the restart actually",
        "restored ingestion.",
    ]
)


def _delete_existing(session: Session) -> None:
    for table in (
        IncidentEventRecord,
        IncidentCheckpointRecord,
        ApprovalRecord,
        TraceLinkRecord,
    ):
        session.exec(delete(table).where(table.incident_id == INCIDENT_ID))
    session.exec(delete(IncidentRecord).where(IncidentRecord.id == INCIDENT_ID))
    session.commit()


def main() -> int:
    now = utc_now()

    with Session(engine) as session:
        _delete_existing(session)
        repo = IncidentRepository(session)

        incident = Incident(
            id=INCIDENT_ID,
            title="Jaguar worker offline after recent deploy",
            severity=IncidentSeverity.SEV1,
            status=IncidentStatus.WAITING_FOR_APPROVAL,
            environment="production",
            product="jaguar",
            mode=IncidentMode.NORMAL,
            stage=IncidentStage.REQUEST_APPROVAL,
            summary=(
                "Halo investigated the blackout and prepared a worker restart; it is holding the "
                "action for operator approval."
            ),
            latest_recommendation=PRE_RECOMMENDATION,
            current_agent="halo-normal",
            current_virtual_model="halo-vm-normal",
            created_at=now,
            updated_at=now,
        )

        approval = Approval(
            incident_id=incident.id,
            action_type="jaguar:worker_restart",
            status=ApprovalStatus.PENDING,
            external_system="jaguar-demo",
            external_action_id=ACTION_ID,
            external_status="proposed",
            risk="Medium",
            title="Worker Restart",
            details={
                "demo_local": True,
                "post_recommendation": build_demo_recommendation(ACTION_ID),
                "executed_response": (
                    f"APPROVED action_request {ACTION_ID} — Jaguar accepted the request and "
                    "ops-runner executed the worker restart."
                ),
            },
            requested_at=now + timedelta(seconds=4),
        )

        incident.approvals = [approval]
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
                    "trace_id": TRACE_ID,
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
        ]
        incident.checkpoints = [
            IncidentCheckpoint(
                incident_id=incident.id,
                stage=IncidentStage.INTAKE,
                state={
                    "reason": "seeded awaiting-approval demo",
                    "mode": IncidentMode.NORMAL,
                    "status": IncidentStatus.OPEN,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now,
            ),
            IncidentCheckpoint(
                incident_id=incident.id,
                stage=IncidentStage.REQUEST_APPROVAL,
                state={
                    "reason": "prepared worker restart, awaiting approval",
                    "mode": IncidentMode.NORMAL,
                    "status": IncidentStatus.WAITING_FOR_APPROVAL,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now + timedelta(seconds=4),
            ),
        ]
        incident.trace_links = [
            TraceLink(
                incident_id=incident.id,
                trace_id=TRACE_ID,
                metadata={
                    "scenario": "jaguar-worker-offline-live-approval",
                    "mode": "normal",
                    "stage": "classify",
                    "cached_summary": DEMO_TRACE_SUMMARY,
                },
                created_at=now,
            )
        ]
        incident.checkpoint_index = len(incident.checkpoints)

        repo.create(incident)
        print(incident.id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
