import os
from pathlib import Path

TEST_DB = Path("test_halo_pytest.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["HALO_DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["HALO_TRUEFOUNDRY_ENABLED"] = "false"
os.environ["HALO_TRUEFOUNDRY_TRACES_ENABLED"] = "false"

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.db.models import (  # noqa: E402
    ApprovalRecord,
    IncidentCheckpointRecord,
    IncidentEventRecord,
    IncidentRecord,
    TraceLinkRecord,
)
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.incident import TraceLink, utc_now  # noqa: E402
from app.repositories.incidents import IncidentRepository  # noqa: E402


def test_incident_persistence_and_custom_apis() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/incidents",
            json={
                "title": "Checkout API elevated 5xx",
                "severity": "sev1",
                "summary": "Persistence test incident",
            },
        )
        assert created.status_code == 201
        incident = created.json()["incident"]
        incident_id = incident["id"]
        assert incident["environment"] == "staging"
        assert incident["product"] == "unspecified-product"

        for _ in range(5):
            run = client.post(
                f"/incidents/{incident_id}/run",
                json={"scenario": "pytest", "demo_run": True},
            )
            assert run.status_code == 200

        detail = client.get(f"/incidents/{incident_id}")
        assert detail.status_code == 200
        detail_payload = detail.json()["incident"]
        assert detail_payload["stage"] == "request_approval"
        assert len(detail_payload["approvals"]) == 1

        approved = client.post(
            f"/incidents/{incident_id}/approve",
            json={"approval_id": detail_payload["approvals"][0]["id"], "approved": True},
        )
        assert approved.status_code == 200

        assert client.get("/health/summary").status_code == 200
        assert len(client.get("/deploys/recent").json()["deploys"]) == 2
        assert len(client.get("/errors/top").json()["errors"]) == 2
        assert client.get(f"/incidents/{incident_id}/context").status_code == 200
        assert len(client.get("/status/events/recent").json()["events"]) == 2
        assert client.get("/runbooks/search", params={"q": "checkout"}).status_code == 200
        assert client.get("/runbooks/checkout-api-5xx").status_code == 200

    with Session(engine) as session:
        repository = IncidentRepository(session)
        reloaded = repository.get(incident_id)
        assert reloaded is not None
        assert reloaded.checkpoint_index == 7
        assert len(reloaded.events) == 8
        assert len(session.exec(select(IncidentRecord)).all()) == 1
        assert len(session.exec(select(IncidentEventRecord)).all()) == 8
        assert len(session.exec(select(IncidentCheckpointRecord)).all()) == 7
        assert len(session.exec(select(ApprovalRecord)).all()) == 1
        assert len(session.exec(select(TraceLinkRecord)).all()) == 5


def test_targeted_chaos_is_not_consumed_by_unrelated_requests() -> None:
    with TestClient(app) as client:
        incident_id = "inc_targeted_demo"
        other_incident_id = "inc_background_request"
        scenario = "bad-deploy-demo"

        armed = client.post(
            "/demo/fail-next",
            params={"incident_id": incident_id, "scenario": scenario},
        )
        assert armed.status_code == 202
        assert armed.json()["incident_id"] == incident_id
        assert armed.json()["scenario"] == scenario

        unrelated = client.get(
            "/health/summary",
            params={"incident_id": other_incident_id, "scenario": scenario},
        )
        assert unrelated.status_code == 200

        no_context = client.get("/health/summary")
        assert no_context.status_code == 200

        matching = client.get(
            "/health/summary",
            params={"incident_id": incident_id, "scenario": scenario},
        )
        assert matching.status_code == 503

        already_consumed = client.get(
            "/health/summary",
            params={"incident_id": incident_id, "scenario": scenario},
        )
        assert already_consumed.status_code == 200

        bad_payload_arm = client.post("/demo/return-bad-payload", params={"scenario": scenario})
        assert bad_payload_arm.status_code == 202
        wrong_scenario = client.get("/deploys/recent", params={"scenario": "background"})
        assert wrong_scenario.status_code == 200
        bad_payload = client.get("/deploys/recent", params={"scenario": scenario})
        assert bad_payload.status_code == 200
        assert bad_payload.json()["malformed"] is True

        incident_arm = client.post("/demo/fail-next", params={"incident_id": incident_id})
        assert incident_arm.status_code == 202
        wrong_incident = client.get(f"/incidents/{other_incident_id}/context")
        assert wrong_incident.status_code == 200
        matching_incident = client.get(f"/incidents/{incident_id}/context")
        assert matching_incident.status_code == 503

        default_target = client.post("/demo/fail-next")
        assert default_target.status_code == 202
        assert default_target.json()["scenario"] == "default-demo"
        assert client.get("/health/summary").status_code == 200
        assert client.get("/health/summary", params={"scenario": "default-demo"}).status_code == 503


def test_trace_identity_and_chronology_survive_repeated_saves() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/incidents",
            json={
                "title": "Trace identity smoke",
                "severity": "sev2",
                "summary": "Trace persistence test",
            },
        )
        assert created.status_code == 201
        incident_id = created.json()["incident"]["id"]

        for scenario in ("trace-a", "trace-b", "trace-c"):
            run = client.post(
                f"/incidents/{incident_id}/run",
                json={"scenario": scenario, "demo_run": True},
            )
            assert run.status_code == 200

    with Session(engine) as session:
        repository = IncidentRepository(session)
        incident = repository.get(incident_id)
        assert incident is not None

        manual_trace = TraceLink(
            incident_id=incident_id,
            trace_id="external-trace-manual",
            metadata={"scenario": "manual"},
            created_at=utc_now(),
        )
        incident.trace_links.append(manual_trace)
        repository.save(incident)

        first_reload = repository.get(incident_id)
        assert first_reload is not None
        first_ids = [trace.id for trace in first_reload.trace_links]
        first_trace_ids = [trace.trace_id for trace in first_reload.trace_links]
        first_created_at = [trace.created_at for trace in first_reload.trace_links]
        assert first_created_at == sorted(first_created_at)

        first_reload.summary = "Saved again without recreating trace rows"
        repository.save(first_reload)
        second_reload = repository.get(incident_id)
        assert second_reload is not None

        assert [trace.id for trace in second_reload.trace_links] == first_ids
        assert [trace.trace_id for trace in second_reload.trace_links] == first_trace_ids
        assert [trace.created_at for trace in second_reload.trace_links] == first_created_at

        trace_rows = session.exec(
            select(TraceLinkRecord)
            .where(TraceLinkRecord.incident_id == incident_id)
            .order_by(TraceLinkRecord.created_at, TraceLinkRecord.id)
        ).all()
        assert [row.id for row in trace_rows] == first_ids
