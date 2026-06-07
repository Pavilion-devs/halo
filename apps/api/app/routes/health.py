from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/readiness")
def readiness() -> dict[str, bool | str | None]:
    return {
        "status": "ready",
        "service": settings.app_name,
        "database_url_configured": bool(settings.database_url),
        "truefoundry_enabled": settings.truefoundry_enabled,
        "truefoundry_base_url_configured": bool(settings.truefoundry_base_url),
        "truefoundry_mcp_server_observe": settings.truefoundry_mcp_server_observe,
        "truefoundry_mcp_server_act": settings.truefoundry_mcp_server_act,
        "truefoundry_guardrails_configured": bool(settings.truefoundry_guardrails),
        "truefoundry_traces_enabled": settings.truefoundry_traces_enabled,
        "truefoundry_traces_base_url": (
            settings.truefoundry_traces_base_url or settings.truefoundry_base_url
        ),
    }
