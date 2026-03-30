# Cipher

Cipher is a memory-first personal assistant backend built with FastAPI and Neo4j.

## Phase Status

Phase 1, Phase 2, and Phase 3 are complete in this repository. The implemented foundation now includes:

- FastAPI application skeleton
- environment-based configuration
- Neo4j client lifecycle management
- schema and constraint files
- project, task, reminder, note, and person models
- graph repository and service layer
- initial CRUD and memory retrieval endpoints
- a rule-based `/assistant/parse-command` endpoint for early command parsing
- sample data seeding for local testing
- Docker-based local startup support
- task lifecycle update and completion flows
- reminder lifecycle, recurrence, and scheduler worker support
- Google Calendar-backed event access and daily briefing basics
- ranked context retrieval for assistant flows
- vendor-ready LLM layer with an OpenAI implementation
- weekly review, project summary, focus suggestions, and follow-up suggestions

See [docs/phase1_status.md](docs/phase1_status.md) for the Phase 1 audit summary.
See [docs/phase2_status.md](docs/phase2_status.md) for the Phase 2 completion summary.
See [docs/phase3_status.md](docs/phase3_status.md) for the Phase 3 completion summary.

## Local Setup

1. Copy `.env.example` to `.env`.
2. Fill in your Neo4j credentials.
3. Install dependencies:

```bash
uv sync --dev
```

4. Apply Neo4j constraints and indexes:

```bash
uv run cipher-apply-schema
```

5. Start the API:

```bash
uv run cipher-api
```

6. Optionally seed sample Phase 1 data:

```bash
uv run cipher-seed-sample-data
```

7. If you want calendar endpoints to use Google Calendar, add your Google OAuth client id and client secret in `.env` and authorize once:

```bash
uv run cipher-google-calendar-auth
```

8. If you want Phase 3 assistant summaries to use OpenAI, add your API key in `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
LLM_REASONING_EFFORT=none
LLM_VERBOSITY=low
LLM_MAX_CONTEXT_ITEMS=12
LLM_MAX_OUTPUT_TOKENS=220
```

These defaults are intentionally budget-friendly. If `OPENAI_API_KEY` is missing, Cipher falls back to deterministic summaries instead of failing.

## Neo4j Connection

Cipher connects directly to your local Neo4j instance with the official Python driver.

Default local settings:

- URI: `neo4j://localhost:7687`
- Browser: `http://localhost:7474`
- Database: `neo4j`

## API Highlights

- `GET /health`
- `GET /version`
- `POST /projects`
- `GET /projects`
- `POST /tasks`
- `GET /tasks`
- `GET /tasks/by-project/{project_id}`
- `PATCH /tasks/{id}`
- `POST /tasks/{id}/complete`
- `GET /tasks/overdue`
- `POST /reminders`
- `GET /reminders`
- `PATCH /reminders/{id}`
- `POST /reminders/{id}/snooze`
- `POST /reminders/{id}/dismiss`
- `POST /calendar/events` (proxies to Google Calendar)
- `GET /calendar/events` (reads from Google Calendar)
- `PATCH /calendar/events/{id}` (updates Google Calendar events)
- `GET /calendar/free-slots` (derived from Google Calendar events)
- `POST /memory/notes`
- `GET /memory/notes`
- `POST /memory/people`
- `GET /memory/people`
- `GET /memory/search`
- `GET /memory/entities/{id}`
- `GET /memory/entities/{id}/related`
- `POST /assistant/parse-command`
- `GET /assistant/daily-briefing`
- `GET /assistant/weekly-review`
- `GET /assistant/project-summary`
- `GET /assistant/focus-suggestions`
- `GET /assistant/follow-up-suggestions`

## Useful Commands

Run a simple Neo4j connectivity check:

```bash
uv run cipher-neo4j-smoke
```

Apply only the schema files again:

```bash
uv run cipher-apply-schema
```

Seed a fresh sample set of project, person, task, reminder, and note data:

```bash
uv run cipher-seed-sample-data
```

Start the reminder scheduler worker:

```bash
uv run cipher-worker
```

## Google Calendar

Cipher no longer treats Neo4j as the main calendar backend.
Calendar endpoints now use Google Calendar as the provider.

To enable them:

1. Create Google Calendar OAuth client credentials.
2. Set `GOOGLE_CALENDAR_CLIENT_ID` and `GOOGLE_CALENDAR_CLIENT_SECRET` in `.env`.
3. Run:

```bash
uv run cipher-google-calendar-auth
```

After that, `GET /calendar/events`, `POST /calendar/events`, `PATCH /calendar/events/{id}`, and `GET /calendar/free-slots` will operate against Google Calendar.

## Phase 3 Assistant

Phase 3 adds a compact retrieval and summarization layer on top of the graph and Google Calendar.

- `GET /assistant/daily-briefing` now includes `generated_summary`, `suggested_focus`, and `llm_meta`
- `GET /assistant/weekly-review` returns wins, risks, and next actions for the week
- `GET /assistant/project-summary?project=...` accepts a project `id`, `code`, or name match
- `GET /assistant/focus-suggestions` proposes focus blocks from ranked tasks plus free slots
- `GET /assistant/follow-up-suggestions` surfaces people-linked follow-up signals

The OpenAI path is intentionally token-efficient:

- top-ranked graph/calendar items only
- short prompt templates
- strict JSON outputs
- low-verbosity defaults
- deterministic fallback when the LLM is unavailable

## Docker Compose

You can also run the API and Neo4j with Docker:

```bash
docker compose up --build
```

This starts:

- Neo4j Browser on `http://localhost:7474`
- API on `http://127.0.0.1:8181`
