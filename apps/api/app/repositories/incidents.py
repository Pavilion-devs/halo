from sqlalchemy import delete
from sqlmodel import Session, select

from app.db.models import (
    ApprovalRecord,
    IncidentCheckpointRecord,
    IncidentEventRecord,
    IncidentRecord,
    TraceLinkRecord,
)
from app.models.incident import (
    Approval,
    Incident,
    IncidentCheckpoint,
    IncidentEvent,
    TraceLink,
)


class IncidentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, incident: Incident) -> Incident:
        self.save(incident)
        return incident

    def list(self) -> list[Incident]:
        records = self.session.exec(
            select(IncidentRecord).order_by(IncidentRecord.created_at.desc())
        ).all()
        return [self._to_domain(record) for record in records]

    def get(self, incident_id: str) -> Incident | None:
        record = self.session.get(IncidentRecord, incident_id)
        if record is None:
            return None
        return self._to_domain(record)

    def save(self, incident: Incident) -> Incident:
        record = self.session.get(IncidentRecord, incident.id)
        if record is None:
            record = IncidentRecord(**self._incident_values(incident))
            self.session.add(record)
        else:
            for key, value in self._incident_values(incident).items():
                setattr(record, key, value)

        self._replace_children(incident)
        self.session.commit()
        return incident

    def _replace_children(self, incident: Incident) -> None:
        for table in (
            IncidentEventRecord,
            IncidentCheckpointRecord,
            ApprovalRecord,
        ):
            self.session.exec(delete(table).where(table.incident_id == incident.id))

        self.session.add_all(
            [
                IncidentEventRecord(
                    id=event.id,
                    incident_id=incident.id,
                    type=event.type,
                    payload=event.payload,
                    created_at=event.created_at,
                )
                for event in incident.events
            ]
        )
        self.session.add_all(
            [
                IncidentCheckpointRecord(
                    id=checkpoint.id,
                    incident_id=incident.id,
                    stage=str(checkpoint.stage),
                    state=checkpoint.state,
                    created_at=checkpoint.created_at,
                )
                for checkpoint in incident.checkpoints
            ]
        )
        self.session.add_all(
            [
                ApprovalRecord(
                    id=approval.id,
                    incident_id=incident.id,
                    action_type=approval.action_type,
                    status=str(approval.status),
                    external_system=approval.external_system,
                    external_action_id=approval.external_action_id,
                    external_status=approval.external_status,
                    risk=approval.risk,
                    title=approval.title,
                    details=approval.details,
                    requested_at=approval.requested_at,
                    resolved_at=approval.resolved_at,
                )
                for approval in incident.approvals
            ]
        )
        self._upsert_trace_links(incident)

    def _upsert_trace_links(self, incident: Incident) -> None:
        retained_ids = {trace.id for trace in incident.trace_links}
        existing_ids = {
            item.id
            for item in self.session.exec(
                select(TraceLinkRecord).where(TraceLinkRecord.incident_id == incident.id)
            ).all()
        }
        stale_ids = existing_ids - retained_ids
        if stale_ids:
            self.session.exec(delete(TraceLinkRecord).where(TraceLinkRecord.id.in_(stale_ids)))

        for trace in incident.trace_links:
            record = self.session.get(TraceLinkRecord, trace.id)
            if record is None:
                self.session.add(
                    TraceLinkRecord(
                        id=trace.id,
                        incident_id=incident.id,
                        trace_id=trace.trace_id,
                        trace_metadata=trace.metadata,
                        created_at=trace.created_at,
                    )
                )
            else:
                record.incident_id = incident.id
                record.trace_id = trace.trace_id
                record.trace_metadata = trace.metadata
                record.created_at = trace.created_at

    def _to_domain(self, record: IncidentRecord) -> Incident:
        incident = Incident(
            id=record.id,
            title=record.title,
            severity=record.severity,
            status=record.status,
            environment=record.environment,
            product=record.product,
            mode=record.mode,
            stage=record.stage,
            summary=record.summary,
            latest_recommendation=record.latest_recommendation,
            current_agent=record.current_agent,
            current_virtual_model=record.current_virtual_model,
            last_failure=record.last_failure,
            fallback_action=record.fallback_action,
            checkpoint_index=record.checkpoint_index,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        incident.events = [
            IncidentEvent(
                id=item.id,
                incident_id=item.incident_id,
                type=item.type,
                payload=item.payload,
                created_at=item.created_at,
            )
            for item in self.session.exec(
                select(IncidentEventRecord)
                .where(IncidentEventRecord.incident_id == record.id)
                .order_by(IncidentEventRecord.created_at)
            ).all()
        ]
        incident.checkpoints = [
            IncidentCheckpoint(
                id=item.id,
                incident_id=item.incident_id,
                stage=item.stage,
                state=item.state,
                created_at=item.created_at,
            )
            for item in self.session.exec(
                select(IncidentCheckpointRecord)
                .where(IncidentCheckpointRecord.incident_id == record.id)
                .order_by(IncidentCheckpointRecord.created_at)
            ).all()
        ]
        incident.approvals = [
            Approval(
                id=item.id,
                incident_id=item.incident_id,
                action_type=item.action_type,
                status=item.status,
                external_system=item.external_system,
                external_action_id=item.external_action_id,
                external_status=item.external_status,
                risk=item.risk,
                title=item.title,
                details=item.details or {},
                requested_at=item.requested_at,
                resolved_at=item.resolved_at,
            )
            for item in self.session.exec(
                select(ApprovalRecord)
                .where(ApprovalRecord.incident_id == record.id)
                .order_by(ApprovalRecord.requested_at)
            ).all()
        ]
        incident.trace_links = [
            TraceLink(
                id=item.id,
                incident_id=item.incident_id,
                trace_id=item.trace_id,
                metadata=item.trace_metadata,
                created_at=item.created_at,
            )
            for item in self.session.exec(
                select(TraceLinkRecord)
                .where(TraceLinkRecord.incident_id == record.id)
                .order_by(TraceLinkRecord.created_at, TraceLinkRecord.id)
            ).all()
        ]
        return incident

    def _incident_values(self, incident: Incident) -> dict:
        return {
            "id": incident.id,
            "title": incident.title,
            "severity": str(incident.severity),
            "status": str(incident.status),
            "environment": incident.environment,
            "product": incident.product,
            "mode": str(incident.mode),
            "stage": str(incident.stage),
            "summary": incident.summary,
            "latest_recommendation": incident.latest_recommendation,
            "current_agent": incident.current_agent,
            "current_virtual_model": incident.current_virtual_model,
            "last_failure": incident.last_failure,
            "fallback_action": incident.fallback_action,
            "checkpoint_index": incident.checkpoint_index,
            "created_at": incident.created_at,
            "updated_at": incident.updated_at,
        }
