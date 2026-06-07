from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["openapi-specs"])

REPO_ROOT = Path(__file__).resolve().parents[4]
OPENAPI_DIR = REPO_ROOT / "infra" / "openapi"
ALLOWED_SPECS = {
    "incident-api.yaml": OPENAPI_DIR / "incident-api.yaml",
    "runbooks-api.yaml": OPENAPI_DIR / "runbooks-api.yaml",
}


@router.get("/openapi/{spec_name}", response_class=PlainTextResponse)
def get_registration_openapi_spec(spec_name: str) -> PlainTextResponse:
    spec_path = ALLOWED_SPECS.get(spec_name)
    if spec_path is None or not spec_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OpenAPI spec not found")
    return PlainTextResponse(spec_path.read_text(), media_type="application/yaml")
