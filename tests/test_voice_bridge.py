from core.models.entities import MemoryRecord, VoiceMessage
from core.utils.dates import utc_now
from services.voice import VoiceBridgeService


class FakeMemory:
    def __init__(self):
        self.writes = []

    def write(self, payload):
        self.writes.append(payload)
        return MemoryRecord(
            id="mem-1",
            content=payload.content,
            kind=payload.kind,
            source=payload.source,
            tags=payload.tags,
            metadata=payload.metadata,
            created_at=utc_now(),
        )


class FakeRouter:
    def short_reply(self, prompt, *, task_class="chat"):
        return "Done."


def test_voice_bridge_stores_summary_not_transcript():
    memory = FakeMemory()
    service = VoiceBridgeService(memory_service=memory, llm_router=FakeRouter())

    reply = service.handle_message(VoiceMessage(utterance="Remind me to review papers."))

    assert reply.reply == "Done."
    assert memory.writes[0].kind == "voice_summary"
    assert memory.writes[0].metadata["transcript_stored"] is False
