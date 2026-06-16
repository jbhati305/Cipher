from uuid import uuid4

from core.models.entities import MemoryWrite, VoiceMessage, VoiceReply
from services.llm.local_router import LocalFirstLLMRouter
from services.memory.service import MemoryService


class VoiceBridgeService:
    def __init__(self, *, memory_service: MemoryService, llm_router: LocalFirstLLMRouter) -> None:
        self._memory_service = memory_service
        self._llm_router = llm_router

    def handle_message(self, payload: VoiceMessage) -> VoiceReply:
        session_id = payload.session_id or str(uuid4())
        reply = self._llm_router.short_reply(
            (
                "You are Cipher's local voice bridge. Reply briefly for speech. "
                f"User said: {payload.utterance}"
            ),
            task_class="chat",
        )
        summary = self._summarize(payload.utterance)
        self._memory_service.write(
            MemoryWrite(
                content=summary,
                kind="voice_summary",
                source=payload.source,
                tags=["voice", payload.source],
                metadata={"session_id": session_id, "transcript_stored": False},
            )
        )
        return VoiceReply(
            session_id=session_id,
            reply=reply,
            stored_summary=summary,
            used_async_processing=reply.startswith("Cipher is processing"),
        )

    @staticmethod
    def _summarize(utterance: str) -> str:
        clean = " ".join(utterance.split())
        if len(clean) <= 180:
            return f"Voice interaction summary: {clean}"
        return f"Voice interaction summary: {clean[:177]}..."
