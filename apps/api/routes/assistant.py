from fastapi import APIRouter, Depends

from apps.api.dependencies import get_parser_service
from core.models.assistant import ParseCommandRequest, ParsedCommand
from services.assistant.parser import AssistantParserService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/parse-command", response_model=ParsedCommand)
def parse_command(
    payload: ParseCommandRequest,
    service: AssistantParserService = Depends(get_parser_service),
) -> ParsedCommand:
    return service.parse(payload.text)
