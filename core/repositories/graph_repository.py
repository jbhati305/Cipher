from collections.abc import Iterable
from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from neo4j import Driver, ManagedTransaction

from core.models.entities import (
    EntityDetail,
    EntityType,
    NoteCreate,
    NoteRead,
    PersonCreate,
    PersonRead,
    ProjectCreate,
    ProjectRead,
    RelatedEntity,
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


class Neo4jGraphRepository:
    CODE_SEQUENCE_WIDTH = 6

    def __init__(self, driver: Driver, database: str) -> None:
        self._driver = driver
        self._database = database

    def create_project(self, payload: ProjectCreate) -> ProjectRead:
        now = utc_now()
        properties = {
            "id": self._new_id(),
            "name": payload.name,
            "description": payload.description,
            "status": payload.status.value,
            "priority": payload.priority.value,
            "created_at": now,
            "updated_at": now,
        }
        with self._driver.session(database=self._database) as session:
            node = session.execute_write(self._create_entity_node, "Project", "PRJ", properties)
        return ProjectRead(**node)

    def list_projects(self) -> list[ProjectRead]:
        query = """
        MATCH (p:Project)
        RETURN p
        ORDER BY p.updated_at DESC
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(query)
            return [
                ProjectRead(**self._normalize_properties(dict(record["p"])))
                for record in records
            ]

    def create_person(self, payload: PersonCreate) -> PersonRead:
        now = utc_now()
        properties = {
            "id": self._new_id(),
            "name": payload.name,
            "relationship_type": payload.relationship_type,
            "notes": payload.notes,
            "created_at": now,
            "updated_at": now,
        }
        with self._driver.session(database=self._database) as session:
            node = session.execute_write(self._create_entity_node, "Person", "PER", properties)
        return PersonRead(**node)

    def list_people(self) -> list[PersonRead]:
        query = """
        MATCH (p:Person)
        RETURN p
        ORDER BY p.updated_at DESC
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(query)
            return [
                PersonRead(**self._normalize_properties(dict(record["p"])))
                for record in records
            ]

    def create_task(self, payload: TaskCreate) -> TaskRead:
        now = utc_now()
        task_id = self._new_id()
        properties = {
            "id": task_id,
            "title": payload.title,
            "description": payload.description,
            "status": payload.status.value,
            "priority": payload.priority.value,
            "deadline": payload.deadline,
            "estimated_effort": payload.estimated_effort,
            "created_at": now,
            "updated_at": now,
        }
        with self._driver.session(database=self._database) as session:
            session.execute_write(self._create_entity_node, "Task", "TSK", properties)
            if payload.project_id:
                session.execute_write(
                    self._create_relationship,
                    source_id=task_id,
                    relationship_type="BELONGS_TO",
                    target_id=payload.project_id,
                )
            for related_id in payload.related_entity_ids:
                session.execute_write(
                    self._create_relationship,
                    source_id=task_id,
                    relationship_type="RELATES_TO",
                    target_id=related_id,
                )
            record = session.execute_read(self._get_task_record, task_id)
        return self._map_task_record(record)

    def list_tasks(
        self,
        *,
        status: TaskStatus | None = None,
        project_id: str | None = None,
    ) -> list[TaskRead]:
        query = """
        MATCH (t:Task)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:Project)
        WITH t, collect(DISTINCT p.id)[0] AS project_id
        WHERE ($status IS NULL OR t.status = $status)
          AND ($project_id IS NULL OR project_id = $project_id)
        OPTIONAL MATCH (t)-[:RELATES_TO]->(related)
        RETURN t, project_id, collect(DISTINCT related.id) AS related_entity_ids
        ORDER BY t.created_at DESC
        """
        params = {
            "status": status.value if status else None,
            "project_id": project_id,
        }
        with self._driver.session(database=self._database) as session:
            records = session.run(query, params)
            return [self._map_task_record(record) for record in records]

    def list_overdue_tasks(self) -> list[TaskRead]:
        query = """
        MATCH (t:Task)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:Project)
        WITH t, collect(DISTINCT p.id)[0] AS project_id
        WHERE t.deadline IS NOT NULL
          AND t.deadline < datetime()
          AND NOT t.status IN ['completed', 'archived']
        OPTIONAL MATCH (t)-[:RELATES_TO]->(related)
        RETURN t, project_id, collect(DISTINCT related.id) AS related_entity_ids
        ORDER BY t.deadline ASC
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(query)
            return [self._map_task_record(record) for record in records]

    def list_tasks_due_between(self, *, start: datetime, end: datetime) -> list[TaskRead]:
        query = """
        MATCH (t:Task)
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:Project)
        WITH t, collect(DISTINCT p.id)[0] AS project_id
        WHERE t.deadline IS NOT NULL
          AND t.deadline >= $start
          AND t.deadline <= $end
          AND NOT t.status IN ['completed', 'archived']
        OPTIONAL MATCH (t)-[:RELATES_TO]->(related)
        RETURN t, project_id, collect(DISTINCT related.id) AS related_entity_ids
        ORDER BY t.deadline ASC
        """
        params = {"start": start, "end": end}
        with self._driver.session(database=self._database) as session:
            records = session.run(query, params)
            return [self._map_task_record(record) for record in records]

    def update_task(self, task_id: str, payload: TaskUpdate) -> TaskRead | None:
        updates = payload.model_dump(exclude_unset=True)
        properties = self._prepare_updates(
            updates,
            excluded_fields={"project_id", "related_entity_ids"},
        )
        project_was_provided = "project_id" in payload.model_fields_set
        related_entities_were_provided = "related_entity_ids" in payload.model_fields_set

        with self._driver.session(database=self._database) as session:
            record = session.execute_write(
                self._update_task_entity,
                task_id,
                properties,
                project_was_provided,
                updates.get("project_id"),
                related_entities_were_provided,
                updates.get("related_entity_ids"),
            )
        if record is None:
            return None
        return self._map_task_record(record)

    def complete_task(self, task_id: str) -> TaskRead | None:
        return self.update_task(task_id, TaskUpdate(status=TaskStatus.COMPLETED))

    def create_reminder(self, payload: ReminderCreate) -> ReminderRead:
        now = utc_now()
        reminder_id = self._new_id()
        properties = {
            "id": reminder_id,
            "title": payload.title,
            "trigger_time": payload.trigger_time,
            "recurrence_rule": payload.recurrence_rule,
            "status": payload.status.value,
            "channel": payload.channel.value,
            "last_triggered_at": None,
            "trigger_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        with self._driver.session(database=self._database) as session:
            session.execute_write(self._create_entity_node, "Reminder", "REM", properties)
            for related_id in payload.related_entity_ids:
                session.execute_write(
                    self._create_relationship,
                    source_id=reminder_id,
                    relationship_type="ABOUT",
                    target_id=related_id,
                )
            record = session.execute_read(self._get_reminder_record, reminder_id)
        return self._map_reminder_record(record)

    def list_reminders(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[ReminderRead]:
        query = """
        MATCH (r:Reminder)
        WHERE ($start IS NULL OR r.trigger_time >= $start)
          AND ($end IS NULL OR r.trigger_time <= $end)
        OPTIONAL MATCH (r)-[:ABOUT]->(related)
        RETURN r, collect(DISTINCT related.id) AS related_entity_ids
        ORDER BY r.trigger_time ASC
        """
        params = {"start": start, "end": end}
        with self._driver.session(database=self._database) as session:
            records = session.run(query, params)
            return [self._map_reminder_record(record) for record in records]

    def list_schedulable_reminders(self, *, start: datetime, end: datetime) -> list[ReminderRead]:
        query = """
        MATCH (r:Reminder)
        WHERE r.trigger_time >= $start
          AND r.trigger_time <= $end
          AND r.status IN ['scheduled', 'snoozed']
        OPTIONAL MATCH (r)-[:ABOUT]->(related)
        RETURN r, collect(DISTINCT related.id) AS related_entity_ids
        ORDER BY r.trigger_time ASC
        """
        params = {"start": start, "end": end}
        with self._driver.session(database=self._database) as session:
            records = session.run(query, params)
            return [self._map_reminder_record(record) for record in records]

    def get_reminder(self, reminder_id: str) -> ReminderRead | None:
        with self._driver.session(database=self._database) as session:
            record = session.execute_read(self._get_reminder_record, reminder_id)
        if record is None:
            return None
        return self._map_reminder_record(record)

    def update_reminder(self, reminder_id: str, payload: ReminderUpdate) -> ReminderRead | None:
        updates = payload.model_dump(exclude_unset=True)
        properties = self._prepare_updates(
            updates,
            excluded_fields={"related_entity_ids"},
        )
        related_entities_were_provided = "related_entity_ids" in payload.model_fields_set

        with self._driver.session(database=self._database) as session:
            record = session.execute_write(
                self._update_reminder_entity,
                reminder_id,
                properties,
                related_entities_were_provided,
                updates.get("related_entity_ids"),
            )
        if record is None:
            return None
        return self._map_reminder_record(record)

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
        with self._driver.session(database=self._database) as session:
            record = session.execute_write(
                self._record_reminder_trigger,
                reminder_id,
                triggered_at,
                next_trigger_time,
            )
        if record is None:
            return None
        return self._map_reminder_record(record)

    def create_note(self, payload: NoteCreate) -> NoteRead:
        now = utc_now()
        note_id = self._new_id()
        properties = {
            "id": note_id,
            "title": payload.title,
            "content": payload.content,
            "source": payload.source,
            "created_at": now,
            "updated_at": now,
        }
        with self._driver.session(database=self._database) as session:
            session.execute_write(self._create_entity_node, "Note", "NOT", properties)
            for related_id in payload.related_entity_ids:
                session.execute_write(
                    self._create_relationship,
                    source_id=note_id,
                    relationship_type="RELATES_TO",
                    target_id=related_id,
                )
            record = session.execute_read(self._get_note_record, note_id)
        return self._map_note_record(record)

    def list_notes(self, *, query: str | None = None) -> list[NoteRead]:
        cypher = """
        MATCH (n:Note)
        WHERE (
            $query IS NULL
            OR toLower(coalesce(n.title, '')) CONTAINS $query
            OR toLower(n.content) CONTAINS $query
        )
        OPTIONAL MATCH (n)-[:RELATES_TO]->(related)
        RETURN n, collect(DISTINCT related.id) AS related_entity_ids
        ORDER BY n.updated_at DESC
        """
        params = {"query": query.lower() if query else None}
        with self._driver.session(database=self._database) as session:
            records = session.run(cypher, params)
            return [self._map_note_record(record) for record in records]

    def get_entity(self, entity_id: str) -> EntityDetail | None:
        query = """
        MATCH (n {id: $entity_id})
        RETURN n, labels(n) AS labels
        """
        with self._driver.session(database=self._database) as session:
            record = session.run(query, entity_id=entity_id).single()
            if record is None:
                return None
            node = record["n"]
            entity_type = self._label_to_entity_type(record["labels"])
            return EntityDetail(
                id=node["id"],
                entity_type=entity_type,
                properties=self._normalize_properties(dict(node)),
            )

    def get_related_entities(self, entity_id: str) -> list[RelatedEntity]:
        query = """
        MATCH (n {id: $entity_id})
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN type(r) AS relation_type,
               m,
               labels(m) AS labels,
               CASE
                   WHEN startNode(r).id = $entity_id THEN 'outgoing'
                   ELSE 'incoming'
               END AS direction
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(query, entity_id=entity_id)
            related: list[RelatedEntity] = []
            for record in records:
                node = record["m"]
                if node is None:
                    continue
                entity = EntityDetail(
                    id=node["id"],
                    entity_type=self._label_to_entity_type(record["labels"]),
                    properties=self._normalize_properties(dict(node)),
                )
                related.append(
                    RelatedEntity(
                        relation_type=record["relation_type"],
                        direction=record["direction"],
                        entity=entity,
                    )
                )
            return related

    def search(self, *, query: str, limit: int) -> list[EntityDetail]:
        cypher = """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels)
          AND (
            toLower(coalesce(n.name, '')) CONTAINS $query
            OR toLower(coalesce(n.title, '')) CONTAINS $query
            OR toLower(coalesce(n.description, '')) CONTAINS $query
            OR toLower(coalesce(n.content, '')) CONTAINS $query
          )
        RETURN n, labels(n) AS labels
        LIMIT $limit
        """
        params = {
            "labels": [entity_type.value for entity_type in EntityType],
            "query": query.lower(),
            "limit": limit,
        }
        with self._driver.session(database=self._database) as session:
            records = session.run(cypher, params)
            return [
                EntityDetail(
                    id=record["n"]["id"],
                    entity_type=self._label_to_entity_type(record["labels"]),
                    properties=self._normalize_properties(dict(record["n"])),
                )
                for record in records
            ]

    @staticmethod
    def _create_node(
        tx: ManagedTransaction,
        label: str,
        properties: dict,
    ) -> dict:
        result = tx.run(
            f"CREATE (n:{label}) SET n = $properties RETURN n",
            properties=properties,
        )
        return Neo4jGraphRepository._normalize_properties(dict(result.single()["n"]))

    @staticmethod
    def _create_entity_node(
        tx: ManagedTransaction,
        label: str,
        prefix: str,
        properties: dict,
    ) -> dict:
        created_at = properties["created_at"]
        period = Neo4jGraphRepository._code_period(created_at)
        sequence = tx.run(
            """
            MERGE (counter:Counter {name: $counter_name})
            ON CREATE SET counter.value = 0
            SET counter.value = counter.value + 1
            RETURN counter.value AS sequence
            """,
            counter_name=f"{prefix}:{period}",
        ).single()["sequence"]
        entity_properties = {
            **properties,
            "code": Neo4jGraphRepository._build_entity_code(prefix, created_at, sequence),
        }
        return Neo4jGraphRepository._create_node(tx, label, entity_properties)

    @staticmethod
    def _create_relationship(
        tx: ManagedTransaction,
        *,
        source_id: str,
        relationship_type: str,
        target_id: str,
    ) -> None:
        tx.run(
            f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[:{relationship_type}]->(target)
            """,
            source_id=source_id,
            target_id=target_id,
        ).consume()

    @staticmethod
    def _update_task_entity(
        tx: ManagedTransaction,
        task_id: str,
        properties: dict,
        project_was_provided: bool,
        project_id: str | None,
        related_entities_were_provided: bool,
        related_entity_ids: list[str] | None,
    ):
        if not Neo4jGraphRepository._entity_exists(tx, "Task", task_id):
            return None

        Neo4jGraphRepository._update_node_properties(tx, "Task", task_id, properties)
        if project_was_provided:
            Neo4jGraphRepository._replace_single_relationship(
                tx,
                source_id=task_id,
                relationship_type="BELONGS_TO",
                target_id=project_id,
            )
        if related_entities_were_provided:
            Neo4jGraphRepository._replace_relationships(
                tx,
                source_id=task_id,
                relationship_type="RELATES_TO",
                target_ids=related_entity_ids or [],
            )
        return Neo4jGraphRepository._get_task_record(tx, task_id)

    @staticmethod
    def _update_reminder_entity(
        tx: ManagedTransaction,
        reminder_id: str,
        properties: dict,
        related_entities_were_provided: bool,
        related_entity_ids: list[str] | None,
    ):
        if not Neo4jGraphRepository._entity_exists(tx, "Reminder", reminder_id):
            return None

        Neo4jGraphRepository._update_node_properties(tx, "Reminder", reminder_id, properties)
        if related_entities_were_provided:
            Neo4jGraphRepository._replace_relationships(
                tx,
                source_id=reminder_id,
                relationship_type="ABOUT",
                target_ids=related_entity_ids or [],
            )
        return Neo4jGraphRepository._get_reminder_record(tx, reminder_id)

    @staticmethod
    def _record_reminder_trigger(
        tx: ManagedTransaction,
        reminder_id: str,
        triggered_at: datetime,
        next_trigger_time: datetime | None,
    ):
        record = tx.run(
            """
            MATCH (r:Reminder {id: $reminder_id})
            SET r.last_triggered_at = $triggered_at,
                r.trigger_count = coalesce(r.trigger_count, 0) + 1,
                r.updated_at = $triggered_at,
                r.status = CASE
                    WHEN $next_trigger_time IS NULL THEN 'triggered'
                    ELSE 'scheduled'
                END,
                r.trigger_time = CASE
                    WHEN $next_trigger_time IS NULL THEN r.trigger_time
                    ELSE $next_trigger_time
                END
            RETURN r
            """,
            reminder_id=reminder_id,
            triggered_at=triggered_at,
            next_trigger_time=next_trigger_time,
        ).single()
        if record is None:
            return None
        return Neo4jGraphRepository._get_reminder_record(tx, reminder_id)

    @staticmethod
    def _get_task_record(tx: ManagedTransaction, task_id: str):
        query = """
        MATCH (t:Task {id: $task_id})
        OPTIONAL MATCH (t)-[:BELONGS_TO]->(p:Project)
        WITH t, collect(DISTINCT p.id)[0] AS project_id
        OPTIONAL MATCH (t)-[:RELATES_TO]->(related)
        RETURN t, project_id, collect(DISTINCT related.id) AS related_entity_ids
        """
        return tx.run(query, task_id=task_id).single()

    @staticmethod
    def _get_reminder_record(tx: ManagedTransaction, reminder_id: str):
        query = """
        MATCH (r:Reminder {id: $reminder_id})
        OPTIONAL MATCH (r)-[:ABOUT]->(related)
        RETURN r, collect(DISTINCT related.id) AS related_entity_ids
        """
        return tx.run(query, reminder_id=reminder_id).single()

    @staticmethod
    def _get_note_record(tx: ManagedTransaction, note_id: str):
        query = """
        MATCH (n:Note {id: $note_id})
        OPTIONAL MATCH (n)-[:RELATES_TO]->(related)
        RETURN n, collect(DISTINCT related.id) AS related_entity_ids
        """
        return tx.run(query, note_id=note_id).single()

    @staticmethod
    def _entity_exists(tx: ManagedTransaction, label: str, entity_id: str) -> bool:
        record = tx.run(
            f"MATCH (n:{label} {{id: $entity_id}}) RETURN n.id AS id",
            entity_id=entity_id,
        ).single()
        return record is not None

    @staticmethod
    def _update_node_properties(
        tx: ManagedTransaction,
        label: str,
        entity_id: str,
        properties: dict,
    ) -> None:
        tx.run(
            f"""
            MATCH (n:{label} {{id: $entity_id}})
            SET n += $properties
            """,
            entity_id=entity_id,
            properties=properties,
        ).consume()

    @staticmethod
    def _replace_single_relationship(
        tx: ManagedTransaction,
        *,
        source_id: str,
        relationship_type: str,
        target_id: str | None,
    ) -> None:
        tx.run(
            f"""
            MATCH (source {{id: $source_id}})-[rel:{relationship_type}]->()
            DELETE rel
            """,
            source_id=source_id,
        ).consume()
        if target_id is None:
            return
        Neo4jGraphRepository._create_relationship(
            tx,
            source_id=source_id,
            relationship_type=relationship_type,
            target_id=target_id,
        )

    @staticmethod
    def _replace_relationships(
        tx: ManagedTransaction,
        *,
        source_id: str,
        relationship_type: str,
        target_ids: list[str],
    ) -> None:
        tx.run(
            f"""
            MATCH (source {{id: $source_id}})-[rel:{relationship_type}]->()
            DELETE rel
            """,
            source_id=source_id,
        ).consume()
        if not target_ids:
            return
        tx.run(
            f"""
            MATCH (source {{id: $source_id}})
            UNWIND $target_ids AS target_id
            MATCH (target {{id: target_id}})
            MERGE (source)-[:{relationship_type}]->(target)
            """,
            source_id=source_id,
            target_ids=target_ids,
        ).consume()

    @staticmethod
    def _map_task_record(record) -> TaskRead:
        return TaskRead(
            **Neo4jGraphRepository._normalize_properties(dict(record["t"])),
            project_id=record["project_id"],
            related_entity_ids=Neo4jGraphRepository._clean_ids(record["related_entity_ids"]),
        )

    @staticmethod
    def _map_reminder_record(record) -> ReminderRead:
        return ReminderRead(
            **Neo4jGraphRepository._normalize_properties(dict(record["r"])),
            related_entity_ids=Neo4jGraphRepository._clean_ids(record["related_entity_ids"]),
        )

    @staticmethod
    def _map_note_record(record) -> NoteRead:
        return NoteRead(
            **Neo4jGraphRepository._normalize_properties(dict(record["n"])),
            related_entity_ids=Neo4jGraphRepository._clean_ids(record["related_entity_ids"]),
        )

    @staticmethod
    def _normalize_properties(properties: dict) -> dict:
        return {
            key: Neo4jGraphRepository._normalize_value(value)
            for key, value in properties.items()
        }

    @staticmethod
    def _prepare_updates(updates: dict, *, excluded_fields: set[str]) -> dict:
        normalized_updates: dict = {}
        for key, value in updates.items():
            if key in excluded_fields:
                continue
            if isinstance(value, StrEnum):
                normalized_updates[key] = value.value
            else:
                normalized_updates[key] = value
        normalized_updates["updated_at"] = utc_now()
        return normalized_updates

    @staticmethod
    def _normalize_value(value):
        if isinstance(value, list):
            return [Neo4jGraphRepository._normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {
                key: Neo4jGraphRepository._normalize_value(item)
                for key, item in value.items()
            }
        if hasattr(value, "to_native"):
            return value.to_native()
        return value

    @staticmethod
    def _clean_ids(values: Iterable[str | None]) -> list[str]:
        return [value for value in values if value]

    @staticmethod
    def _label_to_entity_type(labels: list[str]) -> EntityType:
        for label in labels:
            try:
                return EntityType(label)
            except ValueError:
                continue
        return EntityType.NOTE

    @staticmethod
    def _new_id() -> str:
        return str(uuid4())

    @staticmethod
    def _build_entity_code(prefix: str, created_at: datetime, sequence: int) -> str:
        period = Neo4jGraphRepository._code_period(created_at)
        padded_sequence = str(sequence).zfill(Neo4jGraphRepository.CODE_SEQUENCE_WIDTH)
        return f"{prefix}-{period}-{padded_sequence}"

    @staticmethod
    def _code_period(created_at: datetime) -> str:
        return created_at.strftime("%y%m")
