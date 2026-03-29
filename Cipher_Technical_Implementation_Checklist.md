# Cipher — Technical Implementation Checklist for Claude Code

## Purpose

This file is a practical implementation checklist for building **Cipher**, a personal AI assistant focused on:

- persistent personal memory
- tasks
- reminders
- scheduling
- contextual assistance
- later: agents

This document is written as an execution-oriented guide for implementation.

---

# Implementation Order

Build in this order:

1. Repository and environment setup
2. Core backend skeleton
3. Graph database setup
4. Graph schema and constraints
5. Memory service
6. Natural language ingestion
7. Task service
8. Reminder service
9. Scheduler worker
10. Calendar integration
11. Context retrieval
12. LLM orchestration
13. Daily/weekly assistant flows
14. Agent layer
15. Testing, observability, cleanup

Do **not** start with agents before memory, tasks, and reminders are stable.

---

# 0. Global Engineering Rules

- [ ] Keep the system **memory-first**
- [ ] Use the graph as the main source of truth for assistant context
- [ ] Keep business logic in services/use-cases, not in route handlers
- [ ] Keep database access inside repository classes
- [ ] Keep LLM prompts versioned and modular
- [ ] Every write action should be auditable
- [ ] Add logs for extraction, graph writes, scheduler triggers, and agent actions
- [ ] Prefer explicit schema and typed models over loose dict-based code
- [ ] Keep V1 local-friendly and simple
- [ ] Avoid premature multi-agent complexity

---

# 1. Repository Setup

## Goal
Create a clean project structure that can scale.

## Checklist

- [ ] Create monorepo or backend-first repo structure
- [ ] Add `README.md`
- [ ] Add `docs/`
- [ ] Add `apps/api`
- [ ] Add `apps/worker`
- [ ] Add `services/`
- [ ] Add `core/`
- [ ] Add `database/neo4j`
- [ ] Add `tests/`
- [ ] Add `scripts/`
- [ ] Add `.env.example`
- [ ] Add `.gitignore`
- [ ] Add `docker-compose.yml`
- [ ] Add developer setup instructions

## Suggested structure

```text
cipher/
├── README.md
├── docs/
├── apps/
│   ├── api/
│   └── worker/
├── services/
│   ├── memory/
│   ├── tasks/
│   ├── reminders/
│   ├── scheduler/
│   ├── calendar/
│   ├── llm/
│   └── agents/
├── core/
│   ├── models/
│   ├── repositories/
│   ├── usecases/
│   ├── prompts/
│   └── utils/
├── database/
│   └── neo4j/
├── tests/
├── scripts/
├── .env.example
└── docker-compose.yml
```

---

# 2. Environment and Tooling

## Goal
Make local development reproducible.

## Checklist

- [ ] Choose backend stack: Python + FastAPI
- [ ] Create Python project setup
- [ ] Add dependency manager (`uv` or `poetry`)
- [ ] Add formatting (`ruff`, `black` or equivalent)
- [ ] Add type checking (`mypy` if desired)
- [ ] Add test runner (`pytest`)
- [ ] Add environment variable loading
- [ ] Add base settings module
- [ ] Add pre-commit hooks
- [ ] Add Docker support for local Neo4j and app services

## Dependencies to install

- [ ] fastapi
- [ ] uvicorn
- [ ] pydantic
- [ ] neo4j driver
- [ ] apscheduler
- [ ] python-dateutil
- [ ] pytest
- [ ] httpx
- [ ] structlog or logging helper
- [ ] openai/anthropic/other LLM SDK as needed

Optional later:
- [ ] sentence-transformers
- [ ] pgvector / vector db client
- [ ] redis
- [ ] celery / rq if task execution grows

---

# 3. Backend Skeleton

## Goal
Create a clean application foundation.

## Checklist

- [ ] Create FastAPI app entrypoint
- [ ] Create health check route
- [ ] Create version route
- [ ] Add centralized settings/config module
- [ ] Add dependency injection pattern for services
- [ ] Add request/response schemas
- [ ] Add base exception handling
- [ ] Add structured logging
- [ ] Add middleware for request logging
- [ ] Add route groups:
  - [ ] memory
  - [ ] tasks
  - [ ] reminders
  - [ ] calendar
  - [ ] assistant

---

# 4. Neo4j Setup

## Goal
Run Neo4j locally and connect to it from the backend.

## Checklist

- [ ] Add Neo4j service to Docker Compose
- [ ] Configure username/password through env vars
- [ ] Add local connection test script
- [ ] Add database client wrapper
- [ ] Add connection lifecycle management
- [ ] Add retry logic on startup
- [ ] Add simple smoke test query

## Deliverable
Backend can connect to Neo4j and run a simple query successfully.

---

# 5. Graph Schema and Constraints

## Goal
Define the first stable graph model.

## Required node types for V1

- [ ] User
- [ ] Person
- [ ] Project
- [ ] Task
- [ ] Reminder
- [ ] Event
- [ ] Note
- [ ] Goal

## Required relationship types for V1

- [ ] WORKS_ON
- [ ] KNOWS
- [ ] BELONGS_TO
- [ ] ABOUT
- [ ] INVOLVES
- [ ] RELATES_TO
- [ ] BROKEN_INTO
- [ ] DEPENDS_ON
- [ ] HAS_NOTE
- [ ] HAS_TASK
- [ ] HAS_REMINDER
- [ ] SUPPORTS

## Checklist

- [ ] Create `schema.cypher`
- [ ] Create `constraints.cypher`
- [ ] Add uniqueness constraints on `id`
- [ ] Add indexes on high-lookup fields
- [ ] Add migration/apply script for schema
- [ ] Add seed script with sample data
- [ ] Document node properties
- [ ] Document relationship semantics

## Minimum properties

### User
- [ ] id
- [ ] name
- [ ] timezone
- [ ] created_at
- [ ] updated_at

### Person
- [ ] id
- [ ] name
- [ ] relationship_type
- [ ] notes
- [ ] created_at
- [ ] updated_at

### Project
- [ ] id
- [ ] name
- [ ] description
- [ ] status
- [ ] priority
- [ ] created_at
- [ ] updated_at

### Task
- [ ] id
- [ ] title
- [ ] description
- [ ] status
- [ ] priority
- [ ] deadline
- [ ] estimated_effort
- [ ] created_at
- [ ] updated_at

### Reminder
- [ ] id
- [ ] title
- [ ] trigger_time
- [ ] recurrence_rule
- [ ] status
- [ ] channel
- [ ] created_at
- [ ] updated_at

### Event
- [ ] id
- [ ] title
- [ ] start_time
- [ ] end_time
- [ ] location
- [ ] description
- [ ] created_at
- [ ] updated_at

### Note
- [ ] id
- [ ] title
- [ ] content
- [ ] source
- [ ] created_at
- [ ] updated_at

### Goal
- [ ] id
- [ ] title
- [ ] description
- [ ] status
- [ ] target_date
- [ ] created_at
- [ ] updated_at

---

# 6. Domain Models and Repositories

## Goal
Implement typed domain models and graph repositories.

## Checklist

- [ ] Create Pydantic models for all V1 entities
- [ ] Create create/update/read schema variants
- [ ] Create repository interface for graph access
- [ ] Implement Neo4j repository methods:
  - [ ] create_user
  - [ ] create_person
  - [ ] create_project
  - [ ] create_task
  - [ ] create_reminder
  - [ ] create_event
  - [ ] create_note
  - [ ] create_goal
- [ ] Implement fetch methods
- [ ] Implement update methods
- [ ] Implement delete/archive methods
- [ ] Implement relationship creation methods
- [ ] Implement query helpers for linked entities
- [ ] Add repository unit tests

---

# 7. Memory Service

## Goal
Build the core service that manages structured personal memory.

## Checklist

- [ ] Create memory service module
- [ ] Implement entity upsert logic
- [ ] Implement relation upsert logic
- [ ] Implement deduplication logic
- [ ] Implement fuzzy matching rules for repeated people/projects
- [ ] Implement note linking
- [ ] Implement graph query helpers
- [ ] Add “get entity by name” flow
- [ ] Add “get related context” flow
- [ ] Add “search personal memory” flow

## Required queries

- [ ] Get all active projects
- [ ] Get all tasks for project
- [ ] Get reminders in date range
- [ ] Get notes linked to project
- [ ] Get tasks linked to person
- [ ] Get overdue tasks
- [ ] Get active goals
- [ ] Get linked entities for any node

## Deduplication rules to implement

- [ ] Exact match on normalized name where safe
- [ ] Case-insensitive matching
- [ ] Optional alias support
- [ ] Merge repeated project mentions
- [ ] Avoid duplicate person nodes from repeated ingestion
- [ ] Add manual merge path later

---

# 8. Natural Language Ingestion Layer

## Goal
Convert natural language into structured graph operations.

## Supported first intents

- [ ] create_task
- [ ] create_reminder
- [ ] create_note
- [ ] create_event
- [ ] query_agenda
- [ ] query_project_tasks
- [ ] query_reminders
- [ ] update_task_status
- [ ] reschedule_reminder

## Checklist

- [ ] Define intent enum
- [ ] Define extraction schema for each intent
- [ ] Create parsing service
- [ ] Create structured extraction prompt
- [ ] Validate extraction output against schema
- [ ] Add fallback for ambiguous extraction
- [ ] Add normalization for dates/times
- [ ] Add normalization for person/project names
- [ ] Route parsed output to correct service

## Example commands to support

- [ ] “Create a task to set up Neo4j”
- [ ] “Remind me tomorrow at 8 PM to call Rahul”
- [ ] “Add a note that Cipher should be memory-first”
- [ ] “Schedule 2 hours tonight for backend planning”
- [ ] “Show my reminders this week”
- [ ] “What tasks are pending for Cipher?”
- [ ] “Mark Neo4j setup task as done”
- [ ] “Move my reminder to 9 PM”

## Important
The parser should return structured JSON-like output, not directly mutate the graph.

---

# 9. Task Service

## Goal
Implement reliable task management.

## Checklist

- [ ] Create task service
- [ ] Add task create flow
- [ ] Add task update flow
- [ ] Add task completion flow
- [ ] Add task archive flow
- [ ] Add task priority update flow
- [ ] Add task status transitions
- [ ] Add project linking
- [ ] Add person linking
- [ ] Add dependency linking
- [ ] Add task listing filters:
  - [ ] by project
  - [ ] by status
  - [ ] by date
  - [ ] overdue
  - [ ] high priority

## Required statuses

- [ ] pending
- [ ] in_progress
- [ ] blocked
- [ ] completed
- [ ] archived

## Required priorities

- [ ] low
- [ ] medium
- [ ] high
- [ ] urgent

---

# 10. Reminder Service

## Goal
Implement reminders as first-class objects, not just plain notifications.

## Checklist

- [ ] Create reminder service
- [ ] Add one-time reminder creation
- [ ] Add recurring reminder creation
- [ ] Add reminder update flow
- [ ] Add snooze flow
- [ ] Add dismiss flow
- [ ] Add reschedule flow
- [ ] Add reminder history/logging
- [ ] Link reminders to:
  - [ ] task
  - [ ] event
  - [ ] goal
  - [ ] note if needed

## Required recurrence support

- [ ] daily
- [ ] weekly
- [ ] monthly
- [ ] custom RRULE later

## Required status values

- [ ] scheduled
- [ ] triggered
- [ ] snoozed
- [ ] dismissed
- [ ] completed
- [ ] cancelled

---

# 11. Scheduler Worker

## Goal
Actually execute reminder timing and scheduled jobs.

## Checklist

- [ ] Create worker app
- [ ] Add APScheduler setup
- [ ] Load reminders due soon
- [ ] Register one-time jobs
- [ ] Register recurring jobs
- [ ] Handle app restart recovery
- [ ] Ensure no duplicate job registration
- [ ] Mark reminder states on trigger
- [ ] Add notification dispatch abstraction
- [ ] Add logs for fired reminders
- [ ] Add retry/error handling

## V1 delivery channels

- [ ] in-app notification
- [ ] console/log notification for local testing

## V2 later
- [ ] email
- [ ] Telegram
- [ ] WhatsApp
- [ ] push notifications

---

# 12. Calendar Integration

## Goal
Allow Cipher to read and create schedule data.

## Checklist

- [ ] Define calendar provider interface
- [ ] Add local/mock calendar provider first if needed
- [ ] Add Google Calendar integration later
- [ ] Read events in date range
- [ ] Create event
- [ ] Update event
- [ ] Detect overlaps/conflicts
- [ ] Suggest free slots
- [ ] Create focus blocks
- [ ] Sync imported events into graph
- [ ] Link event to people/projects/tasks where relevant

## Required flows

- [ ] “What’s on my calendar tomorrow?”
- [ ] “Block 2 hours tonight for Cipher”
- [ ] “Find me free time on Sunday”
- [ ] “Move this block to 9 PM”

---

# 13. Context Retrieval Layer

## Goal
Fetch the right graph context before sending a prompt to the LLM.

## Checklist

- [ ] Create context retrieval module
- [ ] Define context bundle schema
- [ ] Implement retrieval by intent
- [ ] Implement ranking by relevance
- [ ] Retrieve:
  - [ ] due tasks
  - [ ] overdue tasks
  - [ ] reminders
  - [ ] active goals
  - [ ] related notes
  - [ ] linked projects
  - [ ] upcoming events
  - [ ] related people
- [ ] Add recency weighting
- [ ] Add urgency weighting
- [ ] Add explicit priority weighting
- [ ] Add graph distance weighting
- [ ] Add pinned memory support later

## Required assistant questions to support

- [ ] “What should I focus on today?”
- [ ] “What’s pending for Cipher?”
- [ ] “What are my priorities this week?”
- [ ] “Who do I need to follow up with?”
- [ ] “What deadlines are approaching?”

---

# 14. LLM Orchestration Layer

## Goal
Use LLMs for extraction, planning, summarization, and assistance.

## Checklist

- [ ] Create LLM client wrapper
- [ ] Separate prompts by function
- [ ] Add extraction prompts
- [ ] Add planning prompts
- [ ] Add summarization prompts
- [ ] Add daily briefing prompt
- [ ] Add weekly review prompt
- [ ] Add output validation
- [ ] Add retry/fallback on malformed output
- [ ] Add token/context logging
- [ ] Add model config through env vars

## Prompt categories

- [ ] intent detection
- [ ] structured extraction
- [ ] daily planning
- [ ] weekly summary
- [ ] task prioritization
- [ ] proactive suggestions
- [ ] note summarization

## Important
LLM output should be grounded in retrieved graph context, not raw hallucinated memory.

---

# 15. Assistant Endpoints and Flows

## Goal
Expose useful user-facing assistant capabilities.

## Checklist

- [ ] Create `/assistant/parse-command`
- [ ] Create `/assistant/daily-briefing`
- [ ] Create `/assistant/weekly-review`
- [ ] Create `/assistant/project-summary`
- [ ] Create `/assistant/focus-suggestions`
- [ ] Create `/assistant/follow-up-suggestions`

## Required flows

### Daily briefing
- [ ] fetch today’s events
- [ ] fetch due tasks
- [ ] fetch overdue tasks
- [ ] fetch reminders
- [ ] fetch free slots
- [ ] generate prioritized summary

### Weekly review
- [ ] fetch completed tasks
- [ ] fetch overdue tasks
- [ ] fetch active projects
- [ ] fetch stalled tasks
- [ ] fetch follow-ups
- [ ] generate review summary

### Project summary
- [ ] fetch project tasks
- [ ] fetch related notes
- [ ] fetch deadlines
- [ ] fetch linked people
- [ ] generate concise summary

---

# 16. API Endpoints Checklist

## Memory
- [ ] POST `/memory/notes`
- [ ] GET `/memory/notes`
- [ ] GET `/memory/search`
- [ ] GET `/memory/entities/{id}`
- [ ] GET `/memory/entities/{id}/related`

## Tasks
- [ ] POST `/tasks`
- [ ] GET `/tasks`
- [ ] PATCH `/tasks/{id}`
- [ ] POST `/tasks/{id}/complete`
- [ ] GET `/tasks/overdue`
- [ ] GET `/tasks/by-project/{project_id}`

## Reminders
- [ ] POST `/reminders`
- [ ] GET `/reminders`
- [ ] PATCH `/reminders/{id}`
- [ ] POST `/reminders/{id}/snooze`
- [ ] POST `/reminders/{id}/dismiss`

## Calendar
- [ ] GET `/calendar/events`
- [ ] POST `/calendar/events`
- [ ] PATCH `/calendar/events/{id}`
- [ ] GET `/calendar/free-slots`

## Assistant
- [ ] POST `/assistant/parse-command`
- [ ] GET `/assistant/daily-briefing`
- [ ] GET `/assistant/weekly-review`
- [ ] GET `/assistant/project-summary`
- [ ] GET `/assistant/focus-suggestions`

---

# 17. Notifications Abstraction

## Goal
Keep reminder delivery pluggable.

## Checklist

- [ ] Define notifier interface
- [ ] Add local notifier implementation
- [ ] Add in-app notifier
- [ ] Add email notifier later
- [ ] Add Telegram notifier later
- [ ] Add delivery logs
- [ ] Add delivery failure handling

---

# 18. Observability and Logging

## Goal
Make debugging easy from day one.

## Checklist

- [ ] Add structured logs for API requests
- [ ] Add logs for graph writes
- [ ] Add logs for LLM extraction output
- [ ] Add logs for reminder registration
- [ ] Add logs for reminder firing
- [ ] Add logs for agent actions
- [ ] Add logs for failed deduplication decisions
- [ ] Add correlation/request IDs
- [ ] Add error monitoring hooks later

## Key events to log

- [ ] entity_created
- [ ] entity_updated
- [ ] relation_created
- [ ] reminder_scheduled
- [ ] reminder_triggered
- [ ] task_completed
- [ ] parser_failed
- [ ] llm_output_invalid
- [ ] scheduler_recovered_jobs

---

# 19. Testing Strategy

## Goal
Make the system reliable enough for real personal use.

## Unit tests

- [ ] repository tests
- [ ] memory service tests
- [ ] task service tests
- [ ] reminder service tests
- [ ] scheduler logic tests
- [ ] parser tests
- [ ] date normalization tests
- [ ] recurrence handling tests

## Integration tests

- [ ] API + Neo4j integration
- [ ] task creation end-to-end
- [ ] reminder creation and scheduler registration
- [ ] daily briefing flow
- [ ] project summary flow
- [ ] graph relationship creation tests

## E2E scenarios

- [ ] “Remind me tomorrow at 8 PM to call Rahul”
- [ ] “Create a task to set up Neo4j for Cipher”
- [ ] “Show my tasks for Cipher”
- [ ] “What should I focus on today?”
- [ ] “Block 2 hours tonight for architecture”
- [ ] “Move reminder to 9 PM”

---

# 20. Security and Guardrails

## Goal
Prevent bad writes and uncontrolled automation.

## Checklist

- [ ] Validate all LLM structured outputs
- [ ] Require explicit confirmation for destructive actions if needed
- [ ] Separate suggest vs execute flows
- [ ] Add safe parsing for dates/times
- [ ] Add idempotency where relevant
- [ ] Prevent duplicate reminder creation from repeated retries
- [ ] Keep secrets in env vars
- [ ] Do not hardcode credentials
- [ ] Add access control layer later if multi-user support appears

---

# 21. Phase-Wise Implementation Plan

## Phase 1 — Memory Foundation

### Must complete
- [ ] repo setup
- [ ] app skeleton
- [ ] Neo4j connection
- [ ] graph schema
- [ ] repository layer
- [ ] memory service
- [ ] basic CRUD
- [ ] basic graph queries

### Success criteria
- [ ] create project
- [ ] create task
- [ ] create note
- [ ] create reminder
- [ ] link entities
- [ ] fetch related context

---

## Phase 2 — Tasks + Reminders + Scheduling

### Must complete
- [ ] task service
- [ ] reminder service
- [ ] scheduler worker
- [ ] recurrence support
- [ ] agenda queries
- [ ] calendar read/write basics

### Success criteria
- [ ] natural language reminder creation works
- [ ] reminders fire on time
- [ ] tasks can be tracked cleanly
- [ ] daily agenda is generated from real data

---

## Phase 3 — Contextual Intelligence

### Must complete
- [ ] context retrieval
- [ ] ranking logic
- [ ] LLM prompt layer
- [ ] daily briefing
- [ ] weekly review
- [ ] project summaries

### Success criteria
- [ ] assistant answers are grounded in graph context
- [ ] summaries are useful and personalized
- [ ] priorities are surfaced correctly

---

## Phase 4 — Agent Layer

### Must complete
- [ ] orchestrator
- [ ] planner agent
- [ ] reminder agent
- [ ] graph maintenance agent
- [ ] basic research agent

### Success criteria
- [ ] agents use shared memory
- [ ] agent actions are logged
- [ ] no hidden isolated state

---

# 22. First Sprint Recommendation

## Sprint 1 target
Get the smallest real version working.

## Sprint 1 checklist

- [ ] Initialize repo
- [ ] Add FastAPI app
- [ ] Add Neo4j via Docker Compose
- [ ] Create schema + constraints
- [ ] Create Project/Task/Reminder/Note models
- [ ] Implement graph repository
- [ ] Implement create task endpoint
- [ ] Implement create reminder endpoint
- [ ] Implement list tasks endpoint
- [ ] Implement reminders by date endpoint
- [ ] Add basic natural language parser for:
  - [ ] create task
  - [ ] create reminder
  - [ ] create note

## Sprint 1 success definition
You can say:
- “Create a task to set up Neo4j”
- “Remind me tomorrow at 8 PM to call Rahul”
- “Add note: Cipher should be memory-first”

And Cipher correctly stores all of them in structured form.

---

# 23. Second Sprint Recommendation

## Sprint 2 checklist

- [ ] Add scheduler worker
- [ ] Add reminder firing
- [ ] Add task status updates
- [ ] Add recurring reminders
- [ ] Add project linking
- [ ] Add today agenda query
- [ ] Add assistant daily briefing endpoint

## Sprint 2 success definition
Cipher becomes actually useful for daily organization.

---

# 24. Nice-to-Have Later

- [ ] vector memory search
- [ ] email integration
- [ ] messaging integration
- [ ] voice input/output
- [ ] mobile app
- [ ] habit streaks
- [ ] relationship dashboards
- [ ] autonomous follow-up assistant
- [ ] document ingestion
- [ ] research memory graph
- [ ] travel planning support

---

# 25. Final Build Rule for Claude Code

When implementing Cipher:

1. Build **memory first**
2. Build **task/reminder execution second**
3. Build **LLM contextual assistance third**
4. Build **agents fourth**

Do not skip the graph foundation.

The graph is what makes Cipher coherent over time.
