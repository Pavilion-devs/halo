import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["openapi-specs"])

# Only these names are ever served — the lookup is allow-listed, so a spec_name
# can never be used for path traversal.
_SPEC_FILES = ("incident-api.yaml", "runbooks-api.yaml")


def _resolve_openapi_dir() -> Path | None:
    """Locate the directory holding the registration OpenAPI specs.

    Resolution order, so it works in the monorepo (canonical specs in
    ``infra/openapi``) *and* in the deployed API image, where only ``apps/api``
    is in the build context and the specs are bundled at ``app/openapi``.

    This never raises: the old ``Path(__file__).resolve().parents[4]`` assumed a
    fixed repo depth and threw ``IndexError`` inside the container (the module
    lives at ``/app/app/routes/specs.py``, which has no 5th parent), taking the
    whole API down at import time. A missing directory now just 404s the route.
    """
    env_dir = os.getenv("HALO_OPENAPI_DIR")
    if env_dir and Path(env_dir).is_dir():
        return Path(env_dir)

    here = Path(__file__).resolve()

    # Repo / local-dev layout: walk up to the monorepo's infra/openapi.
    for parent in here.parents:
        candidate = parent / "infra" / "openapi"
        if candidate.is_dir():
            return candidate

    # Deployed image: specs bundled next to the package (app/openapi).
    bundled = here.parents[1] / "openapi"
    if bundled.is_dir():
        return bundled

    return None


OPENAPI_DIR = _resolve_openapi_dir()


@router.get("/openapi/{spec_name}", response_class=PlainTextResponse)
def get_registration_openapi_spec(spec_name: str) -> PlainTextResponse:
    if spec_name not in _SPEC_FILES or OPENAPI_DIR is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OpenAPI spec not found")
    spec_path = OPENAPI_DIR / spec_name
    if not spec_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OpenAPI spec not found")
    return PlainTextResponse(spec_path.read_text(), media_type="application/yaml")
