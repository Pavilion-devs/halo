from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TraceSummary(BaseModel):
    internal_id: str
    trace_id: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    provisional: bool = False
    lookup_status: str
    live_summary: dict[str, Any] | None = None
    error: str | None = None


class IncidentTracesResponse(BaseModel):
    incident_id: str
    traces: list[TraceSummary]
    error: str | None = None
