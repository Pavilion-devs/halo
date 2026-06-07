RUNBOOKS = {
    "checkout-api-5xx": {
        "slug": "checkout-api-5xx",
        "title": "Checkout API elevated 5xx",
        "summary": "Triage elevated error rates on the checkout API.",
        "steps": [
            "Confirm customer impact and current error budget burn.",
            "Compare alert onset with recent deploys.",
            "Check payment provider latency and timeout rates.",
            "Prepare rollback recommendation if deploy correlation is strong.",
        ],
        "risk_notes": [
            "Do not trigger rollback without approval in production.",
            "Do not expose provider tokens or customer payloads in status updates.",
        ],
    },
    "payment-provider-timeouts": {
        "slug": "payment-provider-timeouts",
        "title": "Payment provider timeout spike",
        "summary": "Validate whether checkout failures come from provider latency.",
        "steps": [
            "Check provider status page and recent timeout counters.",
            "Compare timeout distribution across regions.",
            "Enable read-only monitoring until mitigation is approved.",
        ],
        "risk_notes": [
            "Avoid changing payment routing without explicit approval.",
        ],
    },
}


def search_runbooks(query: str) -> dict:
    normalized = query.lower()
    matches = [
        {
            "slug": runbook["slug"],
            "title": runbook["title"],
            "summary": runbook["summary"],
        }
        for runbook in RUNBOOKS.values()
        if normalized in runbook["slug"].lower()
        or normalized in runbook["title"].lower()
        or normalized in runbook["summary"].lower()
    ]
    return {"query": query, "runbooks": matches}


def get_runbook(slug: str) -> dict | None:
    return RUNBOOKS.get(slug)
