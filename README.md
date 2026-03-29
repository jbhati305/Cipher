# Cipher

Cipher is a memory-first personal assistant backend built with FastAPI and Neo4j.

## Phase 1 Scope

This repository now includes the first usable Phase 1 slice:

- FastAPI application skeleton
- environment-based configuration
- Neo4j client lifecycle management
- schema and constraint files
- project, task, reminder, note, and person models
- graph repository and service layer
- initial CRUD and memory retrieval endpoints
- a rule-based `/assistant/parse-command` endpoint for early command parsing

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
- `GET /tasks/overdue`
- `POST /reminders`
- `GET /reminders`
- `POST /memory/notes`
- `GET /memory/notes`
- `POST /memory/people`
- `GET /memory/people`
- `GET /memory/search`
- `GET /memory/entities/{id}`
- `GET /memory/entities/{id}/related`
- `POST /assistant/parse-command`

## Useful Commands

Run a simple Neo4j connectivity check:

```bash
uv run cipher-neo4j-smoke
```

Apply only the schema files again:

```bash
uv run cipher-apply-schema
```
