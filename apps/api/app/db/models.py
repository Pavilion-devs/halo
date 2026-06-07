from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class IncidentRecord(SQLModel, table=True):
    __tablename__ = "incidents"

    id: str = Field(primary_key=True)
    title: str
    severity: str
    status: str
    environment: str
    product: str
    mode: str
    stage: str
    summary: str | None = None
    latest_recommendation: str | None = None
    current_agent: str
    current_virtual_model: str
    last_failure: str | None = None
    fallback_action: str | None = None
    checkpoint_index: int = 0
    created_at: datetime
    updated_at: datetime


class IncidentEventRecord(SQLModel, table=True):
    __tablename__ = "incident_events"

    id: str = Field(primary_key=True)
    incident_id: str = Field(index=True, foreign_key="incidents.id")
    type: str
    payload: dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime


class IncidentCheckpointRecord(SQLModel, table=True):
    __tablename__ = "incident_checkpoints"

    id: str = Field(primary_key=True)
    incident_id: str = Field(index=True, foreign_key="incidents.id")
    stage: str
    state: dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime


class ApprovalRecord(SQLModel, table=True):
    __tablename__ = "approvals"

    id: str = Field(primary_key=True)
    incident_id: str = Field(index=True, foreign_key="incidents.id")
    action_type: str
    status: str
    external_system: str | None = None
    external_action_id: str | None = Field(default=None, index=True)
    external_status: str | None = None
    risk: str | None = None
    title: str | None = None
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    requested_at: datetime
    resolved_at: datetime | None = None


class TraceLinkRecord(SQLModel, table=True):
    __tablename__ = "trace_links"

    id: str = Field(primary_key=True)
    incident_id: str = Field(index=True, foreign_key="incidents.id")
    trace_id: str = Field(index=True)
    trace_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime
