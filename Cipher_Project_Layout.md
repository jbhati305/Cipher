# Cipher — Personal AI Assistant Project Layout

## Vision

**Cipher** is a personal AI assistant designed to organize life, manage tasks, schedule events, create reminders, maintain memory, and gradually evolve into an agentic personal operating system.

The core idea is:

> **Build Cipher as a memory-first assistant, not an agent-first assistant.**

Instead of starting with many agents, the first versions should focus on:

- storing personal knowledge in a structured way
- organizing tasks, reminders, and schedules
- maintaining persistent memory
- connecting information through a knowledge graph
- using LLMs as an intelligence layer on top of that memory

This approach will make Cipher much more reliable, extensible, and useful in real life.

---

## Core Product Goal

Cipher should eventually help with:

- task management
- scheduling
- reminders
- calendar organization
- note storage
- personal memory
- project tracking
- follow-ups
- routines and habits
- contextual assistance
- later: agent-driven execution

Examples of future usage:

- “What should I focus on today?”
- “Remind me tomorrow at 8 PM to call mom.”
- “Block 2 hours on Sunday for Cipher backend work.”
- “Show me all unfinished tasks related to my personal assistant project.”
- “What meetings and deadlines do I have this week?”
- “Who do I need to follow up with?”
- “Summarize my pending priorities.”

---

## Product Philosophy

Cipher should feel like:

- a **personal executive assistant**
- a **memory layer for life**
- a **planner and organizer**
- eventually a **personal operating system**

It should **not** initially try to be:

- a fully autonomous general agent
- an overcomplicated multi-agent system from day one
- a giant platform with too many integrations before the core works

---

## High-Level Architecture

The right mental model for Cipher is:

```text
User Interface / Chat Layer
           ↓
Intent + Command Understanding
           ↓
Memory Layer (Knowledge Graph)
           ↓
Task / Reminder / Scheduler Layer
           ↓
Tool Layer (Calendar, Notifications, Notes, Email later)
           ↓
LLM Intelligence Layer
```

### Main principle

All intelligence should rely on a **shared memory layer**.

That means:

- tasks should connect to projects
- reminders should connect to tasks/events/goals
- notes should connect to topics/projects/people
- people should connect to meetings/follow-ups/projects
- habits should connect to goals and routines

This is why a **knowledge graph** is the right foundation.

---

# Why a Knowledge Graph First

A normal database stores rows.

A knowledge graph stores:

- entities
- relationships
- context
- meaning

Cipher needs to know not just:

- “there is a task”

but also:

- which project it belongs to
- which person it relates to
- which goal it supports
- which reminder is attached to it
- which notes mention it
- whether it is blocked by something else

That makes a graph a strong foundation for personal memory.

---

## Recommended Database Choice

### Best first option: Neo4j Community Edition

Recommended because:

- mature and widely used
- local setup is straightforward
- graph-native
- uses Cypher query language
- easy to model people, tasks, events, notes, projects, goals, and relationships
- good ecosystem and documentation

### Other possible options

#### Memgraph
Good alternative if you want Cypher-like graph querying with strong performance.

#### Apache AGE
Useful if you want PostgreSQL plus graph querying together.

#### ArangoDB
Good if you want document + graph in one database.

#### SurrealDB
Interesting newer option for multi-model design, but less ideal than Neo4j for a first serious build.

---

# Recommended V1 Stack

## Backend
- Python with **FastAPI**
  - clean
  - easy async support
  - good for APIs
  - strong ecosystem

## Database
- **Neo4j Community Edition** for the knowledge graph

## Scheduler
- **APScheduler** or cron-based background scheduler

## LLM Layer
- API-based LLM calls
- prompt + context retrieval from graph

## Frontend
Start simple:
- CLI
- local web UI
- lightweight chat-style interface

## Notification Layer
Initially:
- in-app reminders
- local notifications
- email/WhatsApp/Telegram later

## Optional Later
- vector search
- embeddings
- semantic memory search
- speech interface
- mobile app

---

# Development Strategy

Build in this exact order:

1. **Knowledge graph schema**
2. **Memory ingestion and storage**
3. **Task and reminder system**
4. **Calendar integration**
5. **LLM contextual retrieval**
6. **Daily/weekly summaries**
7. **Agent layer**
8. **Advanced automation**

This order matters.

If agents come before memory, the system becomes messy and unreliable.

---

# Phase-by-Phase Project Plan

---

# Phase 1 — Foundation and Knowledge Graph

## Goal

Build the persistent memory core of Cipher.

This phase should create the base system that stores your personal information in a structured graph format.

## Main Outcome

At the end of Phase 1, Cipher should work as a **local personal memory system**.

It should be able to store and retrieve:

- who people are
- what projects exist
- what tasks exist
- what notes exist
- what goals exist
- what routines exist
- how all of them are connected

---

## What to Build

### 1. Core domain model

Define the first set of entities.

#### Suggested node types

- `User`
- `Person`
- `Project`
- `Task`
- `Event`
- `Reminder`
- `Note`
- `Goal`
- `Routine`
- `Habit`
- `Preference`
- `Place`
- `Topic`
- `Document`
- `Tag`

#### Suggested relationship types

- `(:User)-[:KNOWS]->(:Person)`
- `(:User)-[:WORKS_ON]->(:Project)`
- `(:Task)-[:BELONGS_TO]->(:Project)`
- `(:Reminder)-[:ABOUT]->(:Task)`
- `(:Event)-[:INVOLVES]->(:Person)`
- `(:Note)-[:RELATES_TO]->(:Project)`
- `(:Goal)-[:BROKEN_INTO]->(:Task)`
- `(:Routine)-[:CONTAINS]->(:Task)`
- `(:Habit)-[:SUPPORTS]->(:Goal)`
- `(:Task)-[:DEPENDS_ON]->(:Task)`
- `(:Document)-[:MENTIONS]->(:Topic)`
- `(:Note)-[:MENTIONS]->(:Person)`
- `(:Project)-[:HAS_TOPIC]->(:Topic)`
- `(:Reminder)-[:TRIGGERS_FOR]->(:Event)`

---

### 2. Graph schema design

Each node should have normalized fields.

#### Example properties

##### User
- `id`
- `name`
- `timezone`
- `created_at`
- `updated_at`

##### Person
- `id`
- `name`
- `relationship_type`
- `contact_info`
- `notes`
- `created_at`
- `updated_at`

##### Project
- `id`
- `name`
- `description`
- `status`
- `priority`
- `created_at`
- `updated_at`

##### Task
- `id`
- `title`
- `description`
- `status`
- `priority`
- `deadline`
- `estimated_effort`
- `created_at`
- `updated_at`

##### Event
- `id`
- `title`
- `start_time`
- `end_time`
- `location`
- `description`
- `created_at`
- `updated_at`

##### Reminder
- `id`
- `title`
- `trigger_time`
- `recurrence_rule`
- `status`
- `channel`
- `created_at`
- `updated_at`

##### Note
- `id`
- `title`
- `content`
- `source`
- `created_at`
- `updated_at`

##### Goal
- `id`
- `title`
- `description`
- `target_date`
- `status`
- `created_at`
- `updated_at`

---

### 3. Memory ingestion pipeline

Cipher needs a way to convert raw input into structured graph updates.

#### Inputs
- manual notes
- typed tasks
- reminders
- calendar events
- natural language requests
- journal-style entries
- future imported chats/documents

#### Pipeline
```text
Raw Input
   ↓
Intent Detection
   ↓
Entity Extraction
   ↓
Relation Extraction
   ↓
Normalization
   ↓
Deduplication / Matching
   ↓
Graph Upsert
```

#### Example

Input:
> “Remind me tomorrow at 8 PM to call Rahul about Cipher backend.”

Structured extraction:
- Task: call Rahul about Cipher backend
- Person: Rahul
- Project: Cipher
- Reminder trigger: tomorrow 8 PM

Graph operations:
- create or match `Person(Rahul)`
- create or match `Project(Cipher)`
- create `Task(call Rahul about Cipher backend)`
- connect task to Rahul
- connect task to Cipher
- create reminder
- connect reminder to task

---

### 4. CRUD APIs for graph entities

Create APIs/services for:

- create person
- create project
- create task
- create reminder
- create note
- create goal
- list tasks
- fetch project-related tasks
- fetch linked notes
- fetch reminders by date
- update and delete entities

---

### 5. Basic retrieval layer

Cipher should answer structured questions like:

- “What are my active projects?”
- “What tasks belong to Cipher?”
- “What reminders do I have this week?”
- “Which notes mention Rahul?”
- “What goals are still active?”

---

## Deliverables for Phase 1

### Functional
- local graph database running
- graph schema implemented
- ingestion pipeline working
- entity creation and updates working
- basic retrieval queries working

### Product
- Cipher can store and fetch structured personal memory

---

## Phase 1 Checklist

- [ ] Set up Neo4j locally
- [ ] Define schema and entity types
- [ ] Define relation types
- [ ] Write graph repository layer
- [ ] Create service layer for memory operations
- [ ] Build ingestion pipeline
- [ ] Add deduplication logic for repeated entities
- [ ] Create CRUD APIs
- [ ] Test with sample personal data
- [ ] Validate graph querying

---

# Phase 2 — Tasks, Reminders, and Scheduling

## Goal

Make Cipher useful in daily life by adding execution around time and planning.

At this stage, Cipher becomes an actual organizer.

---

## Main Outcome

Cipher should now be able to:

- create and manage tasks
- create one-time reminders
- create recurring reminders
- schedule events or time blocks
- move/reschedule reminders and tasks
- show daily and weekly agenda

---

## What to Build

### 1. Task management system

Each task should support:

- title
- description
- status
- priority
- due date
- estimated effort
- linked project
- linked people
- tags
- recurrence if needed
- dependency links

#### Task statuses
- pending
- in_progress
- blocked
- completed
- archived

#### Priorities
- low
- medium
- high
- urgent

---

### 2. Reminder engine

Support:

- one-time reminders
- recurring reminders
- snooze
- dismiss
- reschedule
- reminder history
- link reminder to task/event/note/goal

#### Reminder examples
- “Remind me tomorrow at 7.”
- “Remind me every Monday to review goals.”
- “Remind me 30 minutes before my meeting.”
- “Snooze this for 20 minutes.”

---

### 3. Scheduling system

Start with simple time blocking.

Support:

- create event
- create focus block
- suggest available slots
- detect overlaps/conflicts
- move events
- assign task to a time block

#### Examples
- “Block 2 hours tonight for Cipher architecture.”
- “Schedule gym tomorrow morning.”
- “Move my study block from 7 to 9.”
- “What free time do I have on Sunday?”

---

### 4. Calendar integration layer

This should be initially simple.

Features:
- read calendar events
- create events
- create time blocks
- detect conflicts
- sync selected events into graph

The graph should store event relationships, even if source calendar is external.

---

### 5. Natural language command parsing

Cipher should interpret user requests into actions.

#### Example flow

Input:
> “Remind me every Monday at 9 AM to review my weekly goals.”

Parser output:
- intent: create_reminder
- title: review my weekly goals
- recurrence: weekly Monday 9 AM
- related entity: Goal Review

Action:
- create reminder
- register recurrence rule
- attach to related goal topic if relevant

---

## Deliverables for Phase 2

### Functional
- task manager working
- reminder engine working
- scheduler working
- basic calendar sync/integration working
- natural language input mapped to actions

### Product
Cipher becomes usable as a personal productivity assistant.

---

## Phase 2 Checklist

- [ ] Build task CRUD and status transitions
- [ ] Build reminder scheduler
- [ ] Implement recurrence rules
- [ ] Add snooze/dismiss/reschedule logic
- [ ] Build daily agenda query
- [ ] Build weekly agenda query
- [ ] Add calendar read integration
- [ ] Add calendar write integration
- [ ] Implement conflict detection
- [ ] Add NLP parsing for task/reminder/schedule commands

---

# Phase 3 — Contextual Intelligence Layer

## Goal

Make Cipher intelligent, not just structured.

This is where the LLM becomes truly useful.

---

## Main Outcome

Cipher should retrieve the right context before responding.

It should understand relevance using:

- graph relationships
- recency
- urgency
- frequency
- active projects
- routines
- priorities

---

## What to Build

### 1. Context retrieval engine

Before sending a prompt to the LLM, fetch:

- relevant tasks
- relevant reminders
- related projects
- related notes
- linked people
- recent events
- active goals
- user preferences

#### Example
User asks:
> “What should I focus on today?”

Cipher should retrieve:
- tasks due today
- overdue tasks
- urgent reminders
- calendar events
- active project priorities
- blocked tasks
- time available

Then the LLM can generate a useful daily plan.

---

### 2. Memory ranking

Not all memory should be treated equally.

Build ranking signals such as:

- recency
- explicit importance
- due date closeness
- frequency of mention
- relationship distance
- pinned memory
- project status

---

### 3. Daily briefing

Generate:
- today’s events
- today’s deadlines
- overdue items
- suggested focus blocks
- follow-ups needed
- reminders due

---

### 4. Weekly review

Generate:
- completed tasks
- missed tasks
- overdue tasks
- progress on active goals
- stalled projects
- frequent unfinished work
- people awaiting follow-up

---

### 5. Suggestion engine

Cipher can proactively suggest:

- task scheduling
- reminder creation
- linking notes to projects
- follow-up reminders after meetings
- catching overdue or neglected goals

#### Examples
- “You usually work on Cipher at night. Want me to block 9–11 PM?”
- “This note seems related to the Cipher project. Link it?”
- “You haven’t followed up with Rahul in 6 days.”

---

## Deliverables for Phase 3

### Functional
- retrieval augmentation from graph
- ranked context selection
- daily plan generation
- weekly review generation
- proactive suggestions

### Product
Cipher starts to feel like a real assistant rather than a storage system.

---

## Phase 3 Checklist

- [ ] Build context assembly module
- [ ] Build retrieval ranking logic
- [ ] Add LLM prompt templates for agenda/planning
- [ ] Implement daily briefing flow
- [ ] Implement weekly review flow
- [ ] Implement follow-up suggestions
- [ ] Implement project progress summaries
- [ ] Add memory importance scoring
- [ ] Add pinned memory support

---

# Phase 4 — Agent Layer

## Goal

Add agents on top of shared memory only after the core is stable.

Do not start here.

Agents should be thin execution layers that use the same graph and tools.

---

## Main Outcome

Cipher can now delegate specialized tasks to internal agents.

---

## Suggested Agents

### 1. Planner Agent
Responsibilities:
- break goals into tasks
- suggest weekly plans
- recommend time blocks

### 2. Reminder Agent
Responsibilities:
- monitor due reminders
- suggest reschedules
- detect missed reminders
- generate proactive nudges

### 3. Knowledge Maintenance Agent
Responsibilities:
- merge duplicate entities
- clean graph inconsistencies
- link orphan notes/tasks
- improve relationship quality

### 4. Communication Agent
Responsibilities:
- draft replies
- create follow-up reminders
- summarize messages or emails
- connect communication to people/projects

### 5. Research Agent
Responsibilities:
- fetch information
- summarize findings
- store key facts into graph
- attach research to project/topic nodes

---

## Agent Architecture

```text
User Request
    ↓
Orchestrator
    ↓
Select Agent
    ↓
Agent reads shared graph context
    ↓
Agent uses tools
    ↓
Agent writes results back to graph
```

### Rule
Every agent must:

- read from shared memory
- write to shared memory
- avoid isolated private state

That keeps Cipher coherent.

---

## Deliverables for Phase 4

### Functional
- orchestrator layer
- planner agent
- reminder agent
- graph maintenance workflows
- research/communication agent prototypes

### Product
Cipher becomes semi-agentic while still staying grounded in memory.

---

## Phase 4 Checklist

- [ ] Design orchestrator
- [ ] Define agent interface
- [ ] Build planner agent
- [ ] Build reminder agent
- [ ] Build maintenance agent
- [ ] Build research agent prototype
- [ ] Ensure shared graph reads/writes
- [ ] Add agent logs and observability
- [ ] Add guardrails for unsafe or wrong actions

---

# Phase 5 — Personal Operating System

## Goal

Turn Cipher into a real daily personal command center.

At this phase, it should move from assistant to personal OS.

---

## Main Outcome

Cipher can run day-to-day organization with ongoing context.

It should support:

- morning planning
- end-of-day review
- weekly planning
- follow-up management
- relationship memory
- habit tracking
- long-term goal tracking
- proactive life organization

---

## What to Build

### 1. Morning briefing
Should include:
- today’s schedule
- top priorities
- reminders
- deadlines
- suggested focus blocks
- follow-ups

### 2. End-of-day review
Should include:
- completed tasks
- unfinished tasks
- what slipped
- what to move tomorrow
- lessons/notes captured

### 3. Weekly planning mode
Should include:
- project priorities
- open deadlines
- available focus time
- carry-forward tasks
- goal progress
- follow-ups

### 4. Relationship memory
Track:
- when you last spoke to someone
- follow-up commitments
- project collaboration
- important personal notes where appropriate

### 5. Habit and routine support
Track:
- morning routines
- workout schedule
- learning schedule
- recurring commitments
- habit streaks if desired

---

## Deliverables for Phase 5

### Functional
- recurring briefing flows
- review workflows
- habit and follow-up tracking
- relationship intelligence
- long-term planning support

### Product
Cipher becomes a usable personal life operating system.

---

## Phase 5 Checklist

- [ ] Build morning briefing workflow
- [ ] Build end-of-day review workflow
- [ ] Build weekly planning workflow
- [ ] Add relationship follow-up memory
- [ ] Add habit tracking support
- [ ] Add routine suggestions
- [ ] Add long-term goal dashboards
- [ ] Add project health view

---

# Proposed Repository Structure

```text
cipher/
├── README.md
├── docs/
│   ├── vision.md
│   ├── architecture.md
│   ├── graph-schema.md
│   ├── roadmap.md
│   └── prompting.md
├── apps/
│   ├── api/
│   ├── worker/
│   └── ui/
├── services/
│   ├── memory/
│   ├── scheduler/
│   ├── tasks/
│   ├── reminders/
│   ├── calendar/
│   ├── agents/
│   └── llm/
├── database/
│   ├── neo4j/
│   │   ├── schema.cypher
│   │   ├── constraints.cypher
│   │   └── seed.cypher
│   └── migrations/
├── core/
│   ├── models/
│   ├── repositories/
│   ├── usecases/
│   ├── prompts/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/
│   ├── seed_data.py
│   ├── import_notes.py
│   ├── sync_calendar.py
│   └── run_worker.py
├── .env.example
└── docker-compose.yml
```

---

# Suggested Internal Modules

## memory
Responsibilities:
- graph operations
- entity extraction
- deduplication
- memory retrieval
- context assembly

## tasks
Responsibilities:
- task CRUD
- status changes
- dependencies
- priority handling

## reminders
Responsibilities:
- reminder scheduling
- recurrence
- snoozing
- delivery

## calendar
Responsibilities:
- event sync
- time blocking
- free slot lookup
- conflict detection

## scheduler
Responsibilities:
- background jobs
- trigger execution
- recurring jobs
- notification timing

## llm
Responsibilities:
- prompt building
- context injection
- summarization
- planning responses
- structured extraction

## agents
Responsibilities:
- orchestrator
- planner agent
- reminder agent
- research agent
- maintenance agent

---

# Suggested API Groups

## Memory APIs
- create note
- update note
- list notes
- search memory
- get linked entities
- get project context

## Task APIs
- create task
- update task
- complete task
- list tasks
- list overdue tasks
- list tasks by project

## Reminder APIs
- create reminder
- update reminder
- snooze reminder
- dismiss reminder
- list reminders by date

## Calendar APIs
- list events
- create event
- update event
- find free slots
- create focus block

## Assistant APIs
- parse command
- daily briefing
- weekly summary
- focus suggestions
- project summary

---

# Initial Data Model Example

```text
(User: Jitesh)
   ├── WORKS_ON ──> (Project: Cipher)
   ├── HAS_GOAL ──> (Goal: Build personal assistant)
   ├── HAS_ROUTINE ──> (Routine: Morning planning)
   └── KNOWS ──> (Person: Rahul)

(Project: Cipher)
   ├── HAS_TASK ──> (Task: Build graph schema)
   ├── HAS_TASK ──> (Task: Set up Neo4j)
   ├── HAS_NOTE ──> (Note: Memory-first design)
   └── HAS_TOPIC ──> (Topic: Knowledge graph)

(Task: Build graph schema)
   ├── BELONGS_TO ──> (Project: Cipher)
   ├── SUPPORTS ──> (Goal: Build personal assistant)
   └── HAS_REMINDER ──> (Reminder: Tonight 9 PM)
```

---

# Milestone Plan

## Milestone 1
Graph memory working locally

### Success criteria
- create entities
- connect them
- query them

---

## Milestone 2
Task and reminder workflows working

### Success criteria
- create reminders from natural language
- create tasks
- list agenda

---

## Milestone 3
Calendar and scheduling working

### Success criteria
- schedule blocks
- detect conflicts
- show day/week plan

---

## Milestone 4
LLM contextual assistance working

### Success criteria
- answer daily planning questions using graph memory
- generate useful summaries

---

## Milestone 5
Agent workflows working

### Success criteria
- planner and reminder agents assist reliably
- all agent actions are grounded in graph memory

---

# Engineering Principles

## 1. Memory-first
Persistent memory is the product foundation.

## 2. Graph as source of truth
All important assistant state should be represented in the graph.

## 3. Thin agent layer
Agents should not own hidden state.

## 4. Keep V1 local and simple
Avoid complex distributed architecture too early.

## 5. Start with strong domain modeling
Bad schema early causes pain later.

## 6. Observability matters
Track:
- created entities
- reminder triggers
- agent actions
- failures
- deduplication decisions

## 7. Human override always
Cipher should suggest and assist, not take uncontrolled action.

---

# Risks and How to Avoid Them

## Risk 1: Starting with too many agents
### Fix
Build memory and planner basics first.

## Risk 2: Weak schema design
### Fix
Spend time on entity and relation modeling early.

## Risk 3: Too many integrations too soon
### Fix
Start with local storage + calendar only.

## Risk 4: LLM responses without structured grounding
### Fix
Always retrieve context from graph first.

## Risk 5: Duplicate messy memory
### Fix
Add normalization and deduplication from the start.

---

# Recommended Immediate Next Steps

## Step 1
Set up repo structure.

## Step 2
Set up Neo4j locally.

## Step 3
Write first graph schema:
- User
- Project
- Task
- Reminder
- Note
- Goal
- Person

## Step 4
Implement memory service:
- create entity
- link entity
- query entity

## Step 5
Implement first natural language ingestion flow:
- “Remind me tomorrow to…”
- “Create a task for…”
- “Add note about…”

## Step 6
Implement task and reminder listing.

## Step 7
Add daily briefing prompt with graph retrieval.

---

# What V1 Should Be

Your first strong usable version of Cipher should do only these things well:

- remember important personal entities and relationships
- create tasks
- create reminders
- organize schedule
- answer planning questions using stored memory

That is enough for a strong foundation.

---

# What V1 Should Not Try to Do

Do not try to immediately build:

- many autonomous agents
- full email automation
- full messaging automation
- voice-first system
- huge integration ecosystem
- perfect proactive AI behavior

Those can come later.

---

# Final Guiding Principle

> **Cipher should become your personal operating system by first becoming your trusted memory and planning engine.**

Build the graph first.  
Build organization second.  
Build intelligence third.  
Build agents fourth.

That sequence will save time, reduce rewrites, and make the system much stronger.
