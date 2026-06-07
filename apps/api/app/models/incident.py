from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class IncidentMode(StrEnum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    BLACKOUT = "blackout"


class IncidentSeverity(StrEnum):
    SEV1 = "sev1"
    SEV2 = "sev2"
    SEV3 = "sev3"


class IncidentStatus(StrEnum):
    OPEN = "open"
    RUNNING = "running"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    HANDED_OFF = "handed_off"
    CLOSED = "closed"


class IncidentStage(StrEnum):
    INTAKE = "intake"
    CLASSIFY = "classify"
    GATHER_EVIDENCE = "gather_evidence"
    DRAFT_PLAN = "draft_plan"
    EXECUTE_SAFE_ACTIONS = "execute_safe_actions"
    REQUEST_APPROVAL = "request_approval"
    MONITOR = "monitor"
    HANDOFF_OR_CLOSE = "handoff_or_close"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class IncidentEvent(BaseModel):
    id: str = Field(default_factory=lambda: new_id("evt"))
    incident_id: str
    type: str
    payload: dict
    created_at: datetime = Field(default_factory=utc_now)


class IncidentCheckpoint(BaseModel):
    id: str = Field(default_factory=lambda: new_id("chk"))
    incident_id: str
    stage: IncidentStage
    state: dict
    created_at: datetime = Field(default_factory=utc_now)


class Approval(BaseModel):
    id: str = Field(default_factory=lambda: new_id("app"))
    incident_id: str
    action_type: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    external_system: str | None = None
    external_action_id: str | None = None
    external_status: str | None = None
    risk: str | None = None
    title: str | None = None
    details: dict = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None


class TraceLink(BaseModel):
    id: str = Field(default_factory=lambda: new_id("trl"))
    incident_id: str
    trace_id: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: new_id("inc"))
    title: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    environment: str
    product: str
    mode: IncidentMode = IncidentMode.NORMAL
    stage: IncidentStage = IncidentStage.INTAKE
    summary: str | None = None
    latest_recommendation: str | None = None
    current_agent: str = "halo-normal"
    current_virtual_model: str = "halo-vm-normal"
    last_failure: str | None = None
    fallback_action: str | None = None
    checkpoint_index: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    events: list[IncidentEvent] = Field(default_factory=list)
    checkpoints: list[IncidentCheckpoint] = Field(default_factory=list)
    approvals: list[Approval] = Field(default_factory=list)
    trace_links: list[TraceLink] = Field(default_factory=list)
