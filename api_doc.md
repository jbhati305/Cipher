# Cipher API Documentation

This document is a practical reference for testing the Cipher API with sample personal data and viewing the stored graph in Neo4j Browser.

## Base URLs

- API base URL: `http://127.0.0.1:8181`
- FastAPI Swagger UI: `http://127.0.0.1:8181/docs`
- FastAPI OpenAPI JSON: `http://127.0.0.1:8181/openapi.json`
- Neo4j Browser: `http://localhost:7474`

## Before You Start

From the project root:

```bash
uv sync --dev
uv run cipher-apply-schema
uv run cipher-api
```

In another terminal, confirm the API is healthy:

```bash
curl http://127.0.0.1:8181/health
```

Expected shape:

```json
{
  "status": "ok",
  "app": "Cipher",
  "version": "0.1.0",
  "neo4j": {
    "configured": true,
    "available": true,
    "uri": "neo4j://localhost:7687",
    "database": "neo4j",
    "last_error": null
  }
}
```

## Fastest Way To Explore

Open `http://127.0.0.1:8181/docs` and test each endpoint from the Swagger UI.

If you want to test with terminal commands, use the `curl` examples below.

## Sample Personal Data Flow

This sequence creates:

- one person
- one project
- one task linked to the project and person
- one recurring reminder linked to the person and task
- one note linked to the person, task, and project

### 1. Create a person

```bash
curl -X POST http://127.0.0.1:8181/memory/people \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rahul Sharma",
    "relationship_type": "friend",
    "notes": "Rahul works at Infosys and prefers evening calls."
  }'
```

Example response:

```json
{
  "id": "person-id",
  "code": "PER-2603-000001",
  "created_at": "2026-03-30T06:20:00Z",
  "updated_at": "2026-03-30T06:20:00Z",
  "name": "Rahul Sharma",
  "relationship_type": "friend",
  "notes": "Rahul works at Infosys and prefers evening calls."
}
```

Save the returned `id` as `PERSON_ID`. The returned `code` is the readable public identifier you can use in logs, UI, and support-style workflows.

### 2. Create a project

```bash
curl -X POST http://127.0.0.1:8181/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Health Insurance Renewal",
    "description": "Renew family health insurance before the due date.",
    "status": "active",
    "priority": "high"
  }'
```

Save the returned `id` as `PROJECT_ID`.

### 3. Create a task linked to the project and person

Replace `PERSON_ID` and `PROJECT_ID` with real ids from earlier responses.

```bash
curl -X POST http://127.0.0.1:8181/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Call Rahul about insurance documents",
    "description": "Ask Rahul to send the required PDF documents.",
    "status": "pending",
    "priority": "urgent",
    "deadline": "2026-04-02T18:00:00+05:30",
    "estimated_effort": "30m",
    "project_id": "PROJECT_ID",
    "related_entity_ids": ["PERSON_ID"]
  }'
```

Save the returned `id` as `TASK_ID`.

### 4. Create a recurring reminder linked to the person and task

Replace `PERSON_ID` and `TASK_ID`.

```bash
curl -X POST http://127.0.0.1:8181/reminders \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Follow up with Rahul tomorrow evening",
    "trigger_time": "2026-03-31T19:00:00+05:30",
    "recurrence_rule": "daily",
    "status": "scheduled",
    "channel": "in_app",
    "related_entity_ids": ["PERSON_ID", "TASK_ID"]
  }'
```

Save the returned `id` as `REMINDER_ID`.

### 5. Create a note linked to the project, person, and task

Replace `PERSON_ID`, `PROJECT_ID`, and `TASK_ID`.

```bash
curl -X POST http://127.0.0.1:8181/memory/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Insurance renewal context",
    "content": "Rahul said the salary slip and Aadhaar copy will be shared by tonight. Renewal must be completed this week.",
    "source": "manual-entry",
    "related_entity_ids": ["PERSON_ID", "PROJECT_ID", "TASK_ID"]
  }'
```

Save the returned `id` as `NOTE_ID`.

## Read Back The Data

### People

```bash
curl http://127.0.0.1:8181/memory/people
```

### Projects

```bash
curl http://127.0.0.1:8181/projects
```

### Tasks

```bash
curl http://127.0.0.1:8181/tasks
```

Filter by status:

```bash
curl "http://127.0.0.1:8181/tasks?status=pending"
```

Filter by project:

```bash
curl "http://127.0.0.1:8181/tasks?project_id=PROJECT_ID"
```

Patch a task:

```bash
curl -X PATCH http://127.0.0.1:8181/tasks/TASK_ID \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "priority": "high",
    "estimated_effort": "45m"
  }'
```

Mark a task completed:

```bash
curl -X POST http://127.0.0.1:8181/tasks/TASK_ID/complete
```

List tasks by project with the Phase 2 route:

```bash
curl http://127.0.0.1:8181/tasks/by-project/PROJECT_ID
```

### Reminders

```bash
curl http://127.0.0.1:8181/reminders
```

Patch or reschedule a reminder:

```bash
curl -X PATCH http://127.0.0.1:8181/reminders/REMINDER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_time": "2026-04-01T21:00:00+05:30",
    "status": "scheduled"
  }'
```

Snooze a reminder:

```bash
curl -X POST http://127.0.0.1:8181/reminders/REMINDER_ID/snooze \
  -H "Content-Type: application/json" \
  -d '{
    "until": "2026-04-01T22:00:00+05:30"
  }'
```

Dismiss a reminder:

```bash
curl -X POST http://127.0.0.1:8181/reminders/REMINDER_ID/dismiss
```

### Calendar Events

Cipher now treats Google Calendar as the system of record for calendar data.
These endpoints proxy Google Calendar rather than creating a separate local calendar in Neo4j.

Before using them:

Add these to `.env`:

```env
GOOGLE_CALENDAR_CLIENT_ID=your_google_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_google_client_secret
GOOGLE_CALENDAR_TOKEN_FILE=.secrets/google-calendar-token.json
GOOGLE_CALENDAR_ID=primary
```

Then run:

```bash
uv run cipher-google-calendar-auth
```

List events:

```bash
curl http://127.0.0.1:8181/calendar/events
```

Filter events by range:

```bash
curl "http://127.0.0.1:8181/calendar/events?start=2026-04-01T00:00:00%2B05:30&end=2026-04-02T00:00:00%2B05:30"
```

Patch an event:

```bash
curl -X PATCH http://127.0.0.1:8181/calendar/events/EVENT_ID \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Study room"
  }'
```

Find free slots:

```bash
curl "http://127.0.0.1:8181/calendar/free-slots?start=2026-04-01T08:00:00%2B05:30&end=2026-04-01T22:00:00%2B05:30&duration_minutes=60"
```

### Notes

```bash
curl http://127.0.0.1:8181/memory/notes
```

Search notes by text:

```bash
curl "http://127.0.0.1:8181/memory/notes?query=insurance"
```

### Search across memory

```bash
curl "http://127.0.0.1:8181/memory/search?query=rahul&limit=10"
```

### Fetch a single entity

```bash
curl http://127.0.0.1:8181/memory/entities/PERSON_ID
```

### Fetch related entities for graph inspection

```bash
curl http://127.0.0.1:8181/memory/entities/PERSON_ID/related
```

This is especially useful for confirming that relationships were created correctly.

## Assistant Parser Endpoint

This endpoint only parses a command right now. It does not create data automatically.

```bash
curl -X POST http://127.0.0.1:8181/assistant/parse-command \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Remind me tomorrow at 7 PM to call Rahul about the insurance renewal"
  }'
```

Phase 2 parser examples:

```bash
curl -X POST http://127.0.0.1:8181/assistant/parse-command \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule 2 hours tonight for backend planning"
  }'
```

```bash
curl -X POST http://127.0.0.1:8181/assistant/parse-command \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is on my calendar tomorrow?"
  }'
```

## Daily Briefing

Generate a structured daily agenda from real events, reminders, and tasks:

```bash
curl "http://127.0.0.1:8181/assistant/daily-briefing?date=2026-04-01"
```

If you omit `date`, Cipher uses the current day in the configured timezone.

The Phase 3 version of this endpoint now also returns:

- `generated_summary`
- `suggested_focus`
- `follow_ups`
- `llm_meta`

## Phase 3 Assistant Setup

If you want LLM-backed summaries, add these to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4-nano
LLM_REASONING_EFFORT=none
LLM_VERBOSITY=low
LLM_MAX_CONTEXT_ITEMS=12
LLM_MAX_OUTPUT_TOKENS=220
```

These are the default low-cost settings used by Cipher. If `OPENAI_API_KEY` is missing, the assistant endpoints still work with deterministic fallback summaries.

## Weekly Review

Review the current week:

```bash
curl "http://127.0.0.1:8181/assistant/weekly-review?date=2026-04-01"
```

This returns:

- completed tasks from the week
- overdue tasks
- upcoming task deadlines
- active projects
- follow-up people signals
- concise wins, risks, and next actions

## Project Summary

Summarize a project by its `id`, readable `code`, or name:

```bash
curl "http://127.0.0.1:8181/assistant/project-summary?project=PRJ-2604-000001"
```

You can also use a project name:

```bash
curl "http://127.0.0.1:8181/assistant/project-summary?project=Cipher"
```

## Focus Suggestions

Ask Cipher what to work on next:

```bash
curl "http://127.0.0.1:8181/assistant/focus-suggestions?date=2026-04-01"
```

This combines:

- ranked open tasks
- overdue and due work
- Google Calendar free slots
- concise focus block suggestions

## Follow-Up Suggestions

Ask who needs attention soon:

```bash
curl "http://127.0.0.1:8181/assistant/follow-up-suggestions?days=7"
```

This endpoint looks for people-linked reminder and task signals and returns follow-up suggestions grounded in the graph.

## Worker

Run the reminder scheduler worker in a separate terminal:

```bash
uv run cipher-worker
```

This will:

- load due and upcoming reminders
- register reminder jobs
- fire console notifications
- reschedule recurring reminders
- recover jobs when the worker restarts

## Neo4j Browser: See The Graph

Open:

`http://localhost:7474`

Log in with the values from your `.env`:

- username: `neo4j`
- password: your `NEO4J_PASSWORD`
- database: `neo4j`

### Show everything from Cipher

```cypher
MATCH (n)
RETURN n
LIMIT 100
```

### Show nodes and relationships together

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100
```

### Show one person and everything connected to them

Replace `PERSON_ID`.

```cypher
MATCH (p {id: "PERSON_ID"})-[r]-(connected)
RETURN p, r, connected
```

### Show all task to project links

```cypher
MATCH (t:Task)-[r:BELONGS_TO]->(p:Project)
RETURN t, r, p
```

### Show note links

```cypher
MATCH (n:Note)-[r:RELATES_TO]->(e)
RETURN n, r, e
```

### Show reminder links

```cypher
MATCH (r:Reminder)-[rel:ABOUT]->(e)
RETURN r, rel, e
```

## Relationship Types Used By The API

- `Task -[:BELONGS_TO]-> Project`
- `Task -[:RELATES_TO]-> Entity`
- `Note -[:RELATES_TO]-> Entity`
- `Reminder -[:ABOUT]-> Entity`

That means if you create data using the sample flow above, Neo4j Browser should show connected nodes instead of isolated records.

## Public Codes

Cipher now keeps two identifiers on stored entities:

- `id`: internal UUID used for relationships and lookups
- `code`: human-readable incremental identifier

Current code formats:

- Project: `PRJ-YYMM-000001`
- Task: `TSK-YYMM-000001`
- Reminder: `REM-YYMM-000001`
- Person: `PER-YYMM-000001`
- Note: `NOT-YYMM-000001`

Example:

- `PRJ-2603-000001`

Here:

- `PRJ` is the entity prefix
- `2603` means March 2026
- `000001` is the sequence number for that entity type and month

## Common Issues

### API starts but Neo4j is unavailable

Your `.env` currently allows degraded startup:

```env
ALLOW_DEGRADED_STARTUP=true
```

So the API can start even if Neo4j is down. Check `/health` and make sure:

- `neo4j.configured` is `true`
- `neo4j.available` is `true`
- `neo4j.last_error` is `null`

### The graph looks empty in Neo4j Browser

Check these in order:

1. You actually sent `POST` requests, not just `GET` requests.
2. The API responses returned ids and `201` status.
3. `/health` shows Neo4j as available.
4. You are connected to the same Neo4j database as `.env`, which is `neo4j`.

### Relationship not visible

Relationships are only created when you pass valid ids in:

- `tasks.related_entity_ids`
- `tasks.project_id`
- `reminders.related_entity_ids`
- `notes.related_entity_ids`

If you create items without those ids, Neo4j will store isolated nodes.

## Quick Verification Checklist

1. `uv run cipher-apply-schema`
2. `uv run cipher-api`
3. `curl http://127.0.0.1:8181/health`
4. Create person, project, task, reminder, and note
5. Open `http://127.0.0.1:8181/docs`
6. Open `http://localhost:7474`
7. Run `MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100`

## Verified Locally In This Repo

These checks completed successfully in this workspace:

- `uv run pytest -q`
- `uv run cipher-neo4j-smoke`
