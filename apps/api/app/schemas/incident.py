from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.models.incident import (
    Approval,
    Incident,
    IncidentMode,
    IncidentSeverity,
)


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    severity: IncidentSeverity = IncidentSeverity.SEV2
    environment: str = settings.default_incident_environment
    product: str = settings.default_incident_product
    summary: str | None = None


class IncidentRunRequest(BaseModel):
    scenario: str | None = None
    force_mode: IncidentMode | None = None
    demo_run: bool = False


class IncidentApproveRequest(BaseModel):
    approval_id: str | None = None
    approved: bool = True
    note: str | None = None


class IncidentListResponse(BaseModel):
    incidents: list[Incident]


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident: Incident


class ApprovalResponse(BaseModel):
    incident: Incident
    approval: Approval | None
