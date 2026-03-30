# Phase 3 Status

This file records the current status of Phase 3 for Cipher.

## Conclusion

Phase 3 is complete in this repository.

The main outcomes from `Cipher_Technical_Implementation_Checklist.md` are now present:

- compact context retrieval before assistant generation
- ranking based on urgency, priority, status, deadlines, and project activity
- vendor-ready LLM abstraction with an OpenAI Responses implementation
- structured prompt templates for daily planning and summaries
- assistant endpoints for weekly review, project summary, focus suggestions, and follow-up suggestions
- token/context usage metadata on assistant responses
- deterministic fallback paths when an LLM is not configured

## What Phase 3 Includes Here

- `services/assistant/context.py`
  - builds ranked context bundles from graph data and Google Calendar
- `services/assistant/service.py`
  - generates Phase 3 assistant responses with LLM-or-fallback behavior
- `services/llm/`
  - provider interface, OpenAI implementation, and factory wiring
- `core/prompts/assistant.py`
  - short prompt templates with explicit grounding rules
- new endpoints:
  - `GET /assistant/weekly-review`
  - `GET /assistant/project-summary`
  - `GET /assistant/focus-suggestions`
  - `GET /assistant/follow-up-suggestions`

## Token-Efficiency Defaults

Phase 3 is tuned to spend conservatively by default:

- model default: `gpt-5.4-nano`
- reasoning default: `none`
- verbosity default: `low`
- max context items default: `12`
- max output tokens default: `220`
- note snippets are truncated before prompt assembly

## Runtime Notes

- assistant routes still work without `OPENAI_API_KEY`
- when the LLM is unavailable, Cipher returns deterministic grounded output and marks `llm_meta.fallback_used = true`
- the provider boundary is intentionally narrow so another vendor can be added later without rewriting assistant routes
