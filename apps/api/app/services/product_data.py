from app.models.incident import utc_now


def health_summary() -> dict:
    return {
        "product": "example-product",
        "environment": "staging",
        "overall_status": "degraded",
        "signals": [
            {
                "name": "checkout-api-5xx-rate",
                "status": "elevated",
                "value": 8.4,
                "unit": "percent",
            },
            {
                "name": "checkout-api-p95-latency",
                "status": "elevated",
                "value": 1240,
                "unit": "ms",
            },
        ],
        "updated_at": utc_now().isoformat(),
    }


def recent_deploys() -> dict:
    return {
        "deploys": [
            {
                "id": "dep_20260602_001",
                "service": "checkout-api",
                "version": "2026.06.02.1",
                "status": "succeeded",
                "author": "release-bot",
                "completed_at": "2026-06-02T09:10:00Z",
            },
            {
                "id": "dep_20260601_004",
                "service": "checkout-worker",
                "version": "2026.06.01.4",
                "status": "succeeded",
                "author": "release-bot",
                "completed_at": "2026-06-01T18:22:00Z",
            },
        ]
    }


def top_errors() -> dict:
    return {
        "errors": [
            {
                "signature": "PaymentProviderTimeout",
                "count": 1842,
                "first_seen": "2026-06-02T09:14:00Z",
                "last_seen": "2026-06-02T09:28:00Z",
                "service": "checkout-api",
            },
            {
                "signature": "CartValidationFailed",
                "count": 318,
                "first_seen": "2026-06-02T09:16:00Z",
                "last_seen": "2026-06-02T09:27:00Z",
                "service": "checkout-api",
            },
        ]
    }


def incident_context(incident_id: str) -> dict:
    return {
        "incident_id": incident_id,
        "health": health_summary(),
        "recent_deploys": recent_deploys()["deploys"],
        "top_errors": top_errors()["errors"],
        "candidate_runbooks": ["checkout-api-5xx", "payment-provider-timeouts"],
    }


def recent_status_events() -> dict:
    return {
        "events": [
            {
                "id": "status_001",
                "type": "alert.opened",
                "service": "checkout-api",
                "message": "5xx rate breached sev1 threshold",
                "created_at": "2026-06-02T09:15:00Z",
            },
            {
                "id": "status_002",
                "type": "deploy.completed",
                "service": "checkout-api",
                "message": "Deploy dep_20260602_001 completed before alert onset",
                "created_at": "2026-06-02T09:10:00Z",
            },
        ]
    }
