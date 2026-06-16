from fastapi import APIRouter, Depends

from apps.api.dependencies import get_notion_paper_service, require_hermes
from core.models.entities import PaperRead
from services.notion import NotionPaperService

router = APIRouter(prefix="/notion/papers", tags=["notion"])


@router.post("/sync")
def sync_papers(
    service: NotionPaperService = Depends(get_notion_paper_service),
    _: None = Depends(require_hermes),
) -> dict:
    return service.sync()


@router.get("", response_model=list[PaperRead])
def list_papers(
    service: NotionPaperService = Depends(get_notion_paper_service),
    _: None = Depends(require_hermes),
) -> list[PaperRead]:
    return service.list_papers()
