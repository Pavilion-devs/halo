from fastapi import APIRouter, HTTPException, Query, status

from app.services.chaos import (
    apply_chaos,
    arm_bad_payload_next,
    arm_delay_next,
    arm_fail_next,
)
from app.services.product_data import (
    health_summary,
    incident_context,
    recent_deploys,
    recent_status_events,
    top_errors,
)
from app.services.runbooks import get_runbook, search_runbooks

router = APIRouter(tags=["custom-apis"])


@router.get("/health/summary")
def get_health_summary(
    incident_id: str | None = None, scenario: str | None = None
) -> dict | list:
    return apply_chaos(health_summary(), incident_id=incident_id, scenario=scenario)


@router.get("/deploys/recent")
def get_recent_deploys(
    incident_id: str | None = None, scenario: str | None = None
) -> dict | list:
    return apply_chaos(recent_deploys(), incident_id=incident_id, scenario=scenario)


@router.get("/errors/top")
def get_top_errors(incident_id: str | None = None, scenario: str | None = None) -> dict | list:
    return apply_chaos(top_errors(), incident_id=incident_id, scenario=scenario)


@router.get("/incidents/{incident_id}/context")
def get_incident_context(incident_id: str, scenario: str | None = None) -> dict | list:
    return apply_chaos(incident_context(incident_id), incident_id=incident_id, scenario=scenario)


@router.get("/status/events/recent")
def get_recent_status_events(
    incident_id: str | None = None, scenario: str | None = None
) -> dict | list:
    return apply_chaos(recent_status_events(), incident_id=incident_id, scenario=scenario)


@router.post("/demo/fail-next", status_code=status.HTTP_202_ACCEPTED)
def fail_next_call(
    incident_id: str | None = None, scenario: str | None = None
) -> dict[str, int | str | None]:
    return arm_fail_next(incident_id=incident_id, scenario=scenario)


@router.post("/demo/delay-next", status_code=status.HTTP_202_ACCEPTED)
def delay_next_call(
    delay_ms: int = Query(default=750, ge=0, le=10_000),
    incident_id: str | None = None,
    scenario: str | None = None,
) -> dict[str, int | str | None]:
    return arm_delay_next(delay_ms, incident_id=incident_id, scenario=scenario)


@router.post("/demo/return-bad-payload", status_code=status.HTTP_202_ACCEPTED)
def return_bad_payload(
    incident_id: str | None = None, scenario: str | None = None
) -> dict[str, int | str | None]:
    return arm_bad_payload_next(incident_id=incident_id, scenario=scenario)


@router.get("/runbooks/search")
def runbook_search(q: str = Query(min_length=1)) -> dict:
    return search_runbooks(q)


@router.get("/runbooks/{slug}")
def runbook_detail(slug: str) -> dict:
    runbook = get_runbook(slug)
    if runbook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Runbook not found")
    return runbook
