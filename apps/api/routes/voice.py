from fastapi import APIRouter, Depends

from apps.api.dependencies import get_voice_service, require_alexa
from core.models.entities import VoiceMessage, VoiceReply
from services.voice import VoiceBridgeService

router = APIRouter(prefix="/voice/alexa", tags=["voice"])


@router.post("/message", response_model=VoiceReply)
def handle_message(
    payload: VoiceMessage,
    service: VoiceBridgeService = Depends(get_voice_service),
    _: None = Depends(require_alexa),
) -> VoiceReply:
    return service.handle_message(payload)


@router.post("/session", response_model=VoiceReply)
def handle_session_message(
    payload: VoiceMessage,
    service: VoiceBridgeService = Depends(get_voice_service),
    _: None = Depends(require_alexa),
) -> VoiceReply:
    return service.handle_message(payload)
