from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.models.incident import Incident, IncidentEvent
from app.repositories.incidents import IncidentRepository
from app.schemas.incident import (
    ApprovalResponse,
    IncidentApproveRequest,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentRunRequest,
)
from app.schemas.traces import IncidentTracesResponse
from app.services.jaguar_actions import (
    JaguarActionClient,
    extract_action_texts_from_spans,
    get_jaguar_action_client,
)
from app.services.truefoundry import TrueFoundryAgentService, get_truefoundry_service
from app.services.truefoundry_traces import (
    TraceLookupError,
    TrueFoundryTraceService,
    build_query_window,
    get_trace_service,
)
from app.services.workflow import (
    resolve_approval,
    run_next_step,
    seed_incident,
    sync_external_approvals_from_texts,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])
SessionDep = Annotated[Session, Depends(get_session)]
TrueFoundryDep = Annotated[TrueFoundryAgentService, Depends(get_truefoundry_service)]
TraceDep = Annotated[TrueFoundryTraceService, Depends(get_trace_service)]
JaguarActionDep = Annotated[JaguarActionClient, Depends(get_jaguar_action_client)]


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate, session: SessionDep
) -> IncidentResponse:
    repository = IncidentRepository(session)
    incident = Incident(**payload.model_dump())
    repository.create(seed_incident(incident))
    return IncidentResponse(incident=incident)


@router.get("", response_model=IncidentListResponse)
def list_incidents(session: SessionDep) -> IncidentListResponse:
    repository = IncidentRepository(session)
    return IncidentListResponse(incidents=repository.list())


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: str, session: SessionDep
) -> IncidentResponse:
    repository = IncidentRepository(session)
    return IncidentResponse(incident=_get_incident_or_404(repository, incident_id))


@router.post("/{incident_id}/run", response_model=IncidentResponse)
def run_incident(
    incident_id: str,
    payload: IncidentRunRequest,
    session: SessionDep,
    agent_service: TrueFoundryDep,
) -> IncidentResponse:
    repository = IncidentRepository(session)
    incident = _get_incident_or_404(repository, incident_id)
    repository.save(run_next_step(incident, payload, agent_service))
    return IncidentResponse(incident=incident)


@router.post("/{incident_id}/approve", response_model=ApprovalResponse)
def approve_incident(
    incident_id: str,
    payload: IncidentApproveRequest,
    session: SessionDep,
    jaguar_action_client: JaguarActionDep,
) -> ApprovalResponse:
    repository = IncidentRepository(session)
    incident = _get_incident_or_404(repository, incident_id)
    incident, approval = resolve_approval(incident, payload, jaguar_action_client)
    repository.save(incident)
    return ApprovalResponse(incident=incident, approval=approval)


@router.post("/{incident_id}/sync-approvals", response_model=IncidentResponse)
def sync_incident_approvals(
    incident_id: str,
    session: SessionDep,
    trace_service: TraceDep,
) -> IncidentResponse:
    repository = IncidentRepository(session)
    incident = _get_incident_or_404(repository, incident_id)
    texts = [incident.latest_recommendation, incident.summary]

    if trace_service.should_lookup() and incident.trace_links:
        try:
            spans = trace_service.query_spans(
                [trace.trace_id for trace in incident.trace_links],
                build_query_window(incident.trace_links, trace_service.settings),
            )
            texts.extend(extract_action_texts_from_spans(spans))
        except TraceLookupError as exc:
            incident.events.append(
                IncidentEvent(
                    incident_id=incident.id,
                    type="approval.sync_trace_lookup_failed",
                    payload={"error": str(exc)},
                )
            )

    sync_external_approvals_from_texts(incident, texts, source="trace_or_recommendation")
    repository.save(incident)
    return IncidentResponse(incident=incident)


@router.get("/{incident_id}/traces", response_model=IncidentTracesResponse)
def get_incident_traces(
    incident_id: str,
    session: SessionDep,
    trace_service: TraceDep,
) -> IncidentTracesResponse:
    repository = IncidentRepository(session)
    incident = _get_incident_or_404(repository, incident_id)
    return trace_service.summarize_incident_traces(incident)


def _get_incident_or_404(repository: IncidentRepository, incident_id: str) -> Incident:
    incident = repository.get(incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident
