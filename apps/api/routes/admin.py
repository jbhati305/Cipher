from fastapi import APIRouter, Depends, Request

from apps.api.dependencies import get_export_service, require_admin
from exports import ExportService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/exports")
def export_all(
    service: ExportService = Depends(get_export_service),
    _: None = Depends(require_admin),
) -> dict[str, str]:
    return service.export_all()


@router.get("/sync")
def sync_status(
    request: Request,
    _: None = Depends(require_admin),
) -> dict:
    repository = request.app.state.repository
    memos_client = request.app.state.memos_client
    llm_router = request.app.state.llm_router
    return {
        "storage": repository.health(),
        "memos": memos_client.health(),
        "llm": llm_router.health(),
        "recent_audit_events": repository.list_audit_events(limit=20),
    }


@router.get("/model-routing")
def model_routing(
    request: Request,
    _: None = Depends(require_admin),
) -> dict:
    return request.app.state.model_policy.as_dict()
