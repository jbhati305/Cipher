import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.models.entities import (
    MemoryRecord,
    PaperRead,
    ProjectCreate,
    ProjectRead,
    ReminderCreate,
    ReminderRead,
    ReminderStatus,
    ReminderUpdate,
    TaskCreate,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)
from core.utils.dates import utc_now


class SQLiteRepository:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def health(self) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM audit_events").fetchone()
        return {"sqlite_path": str(self._path), "audit_events": row["count"]}

    def create_project(self, payload: ProjectCreate) -> ProjectRead:
        now = utc_now()
        project_id = self._new_id()
        code = self._new_code("PRJ")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, code, name, description, status, priority, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    code,
                    payload.name,
                    payload.description,
                    payload.status.value,
                    payload.priority.value,
                    self._dt(now),
                    self._dt(now),
                ),
            )
            self._audit(conn, "project.created", project_id, payload.model_dump(mode="json"))
        return self.get_project(project_id)  # type: ignore[return-value]

    def list_projects(self) -> list[ProjectRead]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        return [self._map_project(row) for row in rows]

    def get_project(self, project_id: str) -> ProjectRead | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return self._map_project(row) if row else None

    def create_task(self, payload: TaskCreate) -> TaskRead:
        now = utc_now()
        task_id = self._new_id()
        code = self._new_code("TSK")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, code, title, description, status, priority, deadline, estimated_effort,
                    project_id, related_entity_ids, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    code,
                    payload.title,
                    payload.description,
                    payload.status.value,
                    payload.priority.value,
                    self._dt(payload.deadline),
                    payload.estimated_effort,
                    payload.project_id,
                    self._json(payload.related_entity_ids),
                    self._dt(now),
                    self._dt(now),
                ),
            )
            self._audit(conn, "task.created", task_id, payload.model_dump(mode="json"))
        return self.get_task(task_id)  # type: ignore[return-value]

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_id: str | None = None,
    ) -> list[TaskRead]:
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status.value)
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM tasks {where} ORDER BY created_at DESC",
                params,
            ).fetchall()
        return [self._map_task(row) for row in rows]

    def list_overdue_tasks(self) -> list[TaskRead]:
        now = self._dt(utc_now())
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE deadline IS NOT NULL
                  AND deadline < ?
                  AND status NOT IN ('completed', 'archived')
                ORDER BY deadline ASC
                """,
                (now,),
            ).fetchall()
        return [self._map_task(row) for row in rows]

    def list_tasks_due_between(self, *, start: datetime, end: datetime) -> list[TaskRead]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM tasks
                WHERE deadline IS NOT NULL
                  AND deadline >= ?
                  AND deadline <= ?
                  AND status NOT IN ('completed', 'archived')
                ORDER BY deadline ASC
                """,
                (self._dt(start), self._dt(end)),
            ).fetchall()
        return [self._map_task(row) for row in rows]

    def get_task(self, task_id: str) -> TaskRead | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._map_task(row) if row else None

    def update_task(self, task_id: str, payload: TaskUpdate) -> TaskRead | None:
        current = self.get_task(task_id)
        if current is None:
            return None
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return current
        assignments = []
        params: list[Any] = []
        for key, value in updates.items():
            if key in {"status", "priority"} and value is not None:
                value = value.value
            if key == "deadline":
                value = self._dt(value)
            if key == "related_entity_ids":
                value = self._json(value or [])
            assignments.append(f"{key} = ?")
            params.append(value)
        assignments.append("updated_at = ?")
        params.append(self._dt(utc_now()))
        params.append(task_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ?", params)
            self._audit(conn, "task.updated", task_id, updates)
        return self.get_task(task_id)

    def complete_task(self, task_id: str) -> TaskRead | None:
        return self.update_task(task_id, TaskUpdate(status=TaskStatus.COMPLETED))

    def create_reminder(self, payload: ReminderCreate) -> ReminderRead:
        now = utc_now()
        reminder_id = self._new_id()
        code = self._new_code("REM")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reminders (
                    id, code, title, trigger_time, recurrence_rule, status, channel,
                    last_triggered_at, trigger_count, related_entity_ids, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 0, ?, ?, ?)
                """,
                (
                    reminder_id,
                    code,
                    payload.title,
                    self._dt(payload.trigger_time),
                    payload.recurrence_rule,
                    payload.status.value,
                    payload.channel.value,
                    self._json(payload.related_entity_ids),
                    self._dt(now),
                    self._dt(now),
                ),
            )
            self._audit(conn, "reminder.created", reminder_id, payload.model_dump(mode="json"))
        return self.get_reminder(reminder_id)  # type: ignore[return-value]

    def list_reminders(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[ReminderRead]:
        clauses: list[str] = []
        params: list[Any] = []
        if start:
            clauses.append("trigger_time >= ?")
            params.append(self._dt(start))
        if end:
            clauses.append("trigger_time <= ?")
            params.append(self._dt(end))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM reminders {where} ORDER BY trigger_time ASC",
                params,
            ).fetchall()
        return [self._map_reminder(row) for row in rows]

    def list_schedulable_reminders(self, *, start: datetime, end: datetime) -> list[ReminderRead]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM reminders
                WHERE trigger_time >= ?
                  AND trigger_time <= ?
                  AND status IN ('scheduled', 'snoozed')
                ORDER BY trigger_time ASC
                """,
                (self._dt(start), self._dt(end)),
            ).fetchall()
        return [self._map_reminder(row) for row in rows]

    def get_reminder(self, reminder_id: str) -> ReminderRead | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        return self._map_reminder(row) if row else None

    def update_reminder(self, reminder_id: str, payload: ReminderUpdate) -> ReminderRead | None:
        current = self.get_reminder(reminder_id)
        if current is None:
            return None
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return current
        assignments = []
        params: list[Any] = []
        for key, value in updates.items():
            if key in {"status", "channel"} and value is not None:
                value = value.value
            if key == "trigger_time":
                value = self._dt(value)
            if key == "related_entity_ids":
                value = self._json(value or [])
            assignments.append(f"{key} = ?")
            params.append(value)
        assignments.append("updated_at = ?")
        params.append(self._dt(utc_now()))
        params.append(reminder_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE reminders SET {', '.join(assignments)} WHERE id = ?", params)
            self._audit(conn, "reminder.updated", reminder_id, updates)
        return self.get_reminder(reminder_id)

    def snooze_reminder(self, reminder_id: str, until: datetime) -> ReminderRead | None:
        return self.update_reminder(
            reminder_id,
            ReminderUpdate(trigger_time=until, status=ReminderStatus.SNOOZED),
        )

    def dismiss_reminder(self, reminder_id: str) -> ReminderRead | None:
        return self.update_reminder(reminder_id, ReminderUpdate(status=ReminderStatus.DISMISSED))

    def record_reminder_trigger(
        self,
        reminder_id: str,
        *,
        triggered_at: datetime,
        next_trigger_time: datetime | None,
    ) -> ReminderRead | None:
        current = self.get_reminder(reminder_id)
        if current is None:
            return None
        status_value = ReminderStatus.SCHEDULED if next_trigger_time else ReminderStatus.TRIGGERED
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE reminders
                SET last_triggered_at = ?, trigger_count = trigger_count + 1,
                    trigger_time = COALESCE(?, trigger_time), status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    self._dt(triggered_at),
                    self._dt(next_trigger_time),
                    status_value.value,
                    self._dt(utc_now()),
                    reminder_id,
                ),
            )
            self._audit(
                conn,
                "reminder.triggered",
                reminder_id,
                {"next_trigger_time": self._dt(next_trigger_time)},
            )
        return self.get_reminder(reminder_id)

    def upsert_papers(self, papers: Iterable[PaperRead]) -> int:
        count = 0
        with self._connect() as conn:
            for paper in papers:
                conn.execute(
                    """
                    INSERT INTO papers (id, title, authors, status, url, notion_page_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        authors = excluded.authors,
                        status = excluded.status,
                        url = excluded.url,
                        notion_page_id = excluded.notion_page_id,
                        updated_at = excluded.updated_at
                    """,
                    (
                        paper.id,
                        paper.title,
                        paper.authors,
                        paper.status,
                        paper.url,
                        paper.notion_page_id,
                        self._dt(paper.updated_at),
                    ),
                )
                count += 1
            self._audit(conn, "notion.papers_synced", None, {"count": count})
        return count

    def list_papers(self) -> list[PaperRead]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM papers ORDER BY updated_at DESC, title ASC"
            ).fetchall()
        return [self._map_paper(row) for row in rows]

    def record_memory(self, record: MemoryRecord) -> MemoryRecord:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO memory_events (id, content, kind, source, tags, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.content,
                    record.kind,
                    record.source,
                    self._json(record.tags),
                    self._json(record.metadata),
                    self._dt(record.created_at),
                ),
            )
            self._audit(conn, "memory.recorded", record.id, record.model_dump(mode="json"))
        return record

    def list_memory_events(self, *, limit: int = 50) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_events ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._map_memory(row) for row in rows]

    def list_audit_events(self, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) | {"payload": self._loads(row["payload"])} for row in rows]

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    deadline TEXT,
                    estimated_effort TEXT,
                    project_id TEXT,
                    related_entity_ids TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    trigger_time TEXT NOT NULL,
                    recurrence_rule TEXT,
                    status TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    last_triggered_at TEXT,
                    trigger_count INTEGER NOT NULL DEFAULT 0,
                    related_entity_ids TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,
                    status TEXT,
                    url TEXT,
                    notion_page_id TEXT NOT NULL UNIQUE,
                    updated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS memory_events (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    entity_id TEXT,
                    payload TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _audit(
        self,
        conn: sqlite3.Connection,
        event_type: str,
        entity_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO audit_events (id, event_type, entity_id, payload, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (self._new_id(), event_type, entity_id, self._json(payload), self._dt(utc_now())),
        )

    @staticmethod
    def _new_id() -> str:
        return str(uuid4())

    @staticmethod
    def _new_code(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:8].upper()}"

    @staticmethod
    def _dt(value: datetime | None) -> str | None:
        return value.isoformat() if value else None

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value) if value else None

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, default=str, sort_keys=True)

    @staticmethod
    def _loads(value: str | None, default: Any = None) -> Any:
        if value is None:
            return default
        return json.loads(value)

    def _map_project(self, row: sqlite3.Row) -> ProjectRead:
        return ProjectRead(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            created_at=self._parse_dt(row["created_at"]),
            updated_at=self._parse_dt(row["updated_at"]),
        )

    def _map_task(self, row: sqlite3.Row) -> TaskRead:
        return TaskRead(
            id=row["id"],
            code=row["code"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            deadline=self._parse_dt(row["deadline"]),
            estimated_effort=row["estimated_effort"],
            project_id=row["project_id"],
            related_entity_ids=self._loads(row["related_entity_ids"], []),
            created_at=self._parse_dt(row["created_at"]),
            updated_at=self._parse_dt(row["updated_at"]),
        )

    def _map_reminder(self, row: sqlite3.Row) -> ReminderRead:
        return ReminderRead(
            id=row["id"],
            code=row["code"],
            title=row["title"],
            trigger_time=self._parse_dt(row["trigger_time"]),
            recurrence_rule=row["recurrence_rule"],
            status=row["status"],
            channel=row["channel"],
            last_triggered_at=self._parse_dt(row["last_triggered_at"]),
            trigger_count=row["trigger_count"],
            related_entity_ids=self._loads(row["related_entity_ids"], []),
            created_at=self._parse_dt(row["created_at"]),
            updated_at=self._parse_dt(row["updated_at"]),
        )

    def _map_paper(self, row: sqlite3.Row) -> PaperRead:
        return PaperRead(
            id=row["id"],
            title=row["title"],
            authors=row["authors"],
            status=row["status"],
            url=row["url"],
            notion_page_id=row["notion_page_id"],
            updated_at=self._parse_dt(row["updated_at"]),
        )

    def _map_memory(self, row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            content=row["content"],
            kind=row["kind"],
            source=row["source"],
            tags=self._loads(row["tags"], []),
            metadata=self._loads(row["metadata"], {}),
            created_at=self._parse_dt(row["created_at"]),
        )
