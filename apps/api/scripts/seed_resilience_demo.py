#!/usr/bin/env python3
"""Seed (or reset) a NORMAL-mode incident for the resilience / chaos demo.

This incident sits mid-investigation in NORMAL mode. In the War Room, use the
Operator console to arm a fault ("Fail next tool" / "Delay next tool" / "Bad
payload") and then "Run next step": Halo records the failure and steps the mode
down (NORMAL -> DEGRADED, and again -> BLACKOUT) through its real recovery path.
Re-run this script to reset the incident back to NORMAL.
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
from seed_live_jaguar_demo_incident import DEMO_TRACE_SUMMARY

INCIDENT_ID = "inc_demo_resilience"
TRACE_ID = "019e97822312766daef28a9823b35178"

RECOMMENDATION = "\n".join(
    [
        "## Incident Summary",
        "",
        "**Classification:** SEV-2 — Jaguar ingestion latency climbing",
        "",
        "| Signal | Current state |",
        "| --- | --- |",
        "| **Worker process** | Alive, but heartbeat interval is drifting upward. |",
        "| **Ingestion** | Two of four streams lagging; backlog growing slowly. |",
        "| **Working theory** | Provider-side slowdown; watching before any write action. |",
        "",
        "## Evidence",
        "",
        "- Pulled live worker status and ingestion diagnostics through Jaguar MCP read tools.",
        "- No risky action proposed yet — Halo is still gathering evidence in NORMAL mode.",
        "",
        "_Use the Operator console to inject a fault and watch Halo step down a mode while it keeps working._",
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
            title="Jaguar ingestion latency climbing",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.RUNNING,
            environment="production",
            product="jaguar",
            mode=IncidentMode.NORMAL,
            stage=IncidentStage.GATHER_EVIDENCE,
            summary=(
                "Halo is investigating climbing ingestion latency in NORMAL mode. "
                "Arm a fault in the Operator console and run the next step to watch it degrade."
            ),
            latest_recommendation=RECOMMENDATION,
            current_agent="halo-normal",
            current_virtual_model="halo-vm-normal",
            created_at=now,
            updated_at=now,
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
                    "stage": IncidentStage.GATHER_EVIDENCE,
                    "trace_id": TRACE_ID,
                },
                created_at=now + timedelta(seconds=2),
            ),
        ]
        incident.checkpoints = [
            IncidentCheckpoint(
                incident_id=incident.id,
                stage=IncidentStage.INTAKE,
                state={
                    "reason": "seeded resilience demo",
                    "mode": IncidentMode.NORMAL,
                    "status": IncidentStatus.OPEN,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now,
            ),
            IncidentCheckpoint(
                incident_id=incident.id,
                stage=IncidentStage.GATHER_EVIDENCE,
                state={
                    "reason": "completed gather_evidence",
                    "mode": IncidentMode.NORMAL,
                    "status": IncidentStatus.RUNNING,
                    "agent": "halo-normal",
                    "virtual_model": "halo-vm-normal",
                },
                created_at=now + timedelta(seconds=2),
            ),
        ]
        incident.trace_links = [
            TraceLink(
                incident_id=incident.id,
                trace_id=TRACE_ID,
                metadata={
                    "scenario": "war-room",
                    "mode": "normal",
                    "stage": "gather_evidence",
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
