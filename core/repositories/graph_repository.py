from collections.abc import Iterable
from datetime import datetime
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
    TaskCreate,
    TaskRead,
    TaskStatus,
)
from core.utils.dates import utc_now


class Neo4jGraphRepository:
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
            node = session.execute_write(self._create_node, "Project", properties)
        return ProjectRead(**node)

    def list_projects(self) -> list[ProjectRead]:
        query = """
        MATCH (p:Project)
        RETURN p
        ORDER BY p.updated_at DESC
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(query)
            return [ProjectRead(**dict(record["p"])) for record in records]

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
            node = session.execute_write(self._create_node, "Person", properties)
        return PersonRead(**node)

    def list_people(self) -> list[PersonRead]:
        query = """
        MATCH (p:Person)
        RETURN p
        ORDER BY p.updated_at DESC
        """
        with self._driver.session(database=self._database) as session:
            records = session.run(query)
            return [PersonRead(**dict(record["p"])) for record in records]

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
            session.execute_write(self._create_node, "Task", properties)
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
            "created_at": now,
            "updated_at": now,
        }
        with self._driver.session(database=self._database) as session:
            session.execute_write(self._create_node, "Reminder", properties)
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
            session.execute_write(self._create_node, "Note", properties)
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
            return EntityDetail(id=node["id"], entity_type=entity_type, properties=dict(node))

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
                    properties=dict(node),
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
                    properties=dict(record["n"]),
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
        return dict(result.single()["n"])

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
    def _map_task_record(record) -> TaskRead:
        return TaskRead(
            **dict(record["t"]),
            project_id=record["project_id"],
            related_entity_ids=Neo4jGraphRepository._clean_ids(record["related_entity_ids"]),
        )

    @staticmethod
    def _map_reminder_record(record) -> ReminderRead:
        return ReminderRead(
            **dict(record["r"]),
            related_entity_ids=Neo4jGraphRepository._clean_ids(record["related_entity_ids"]),
        )

    @staticmethod
    def _map_note_record(record) -> NoteRead:
        return NoteRead(
            **dict(record["n"]),
            related_entity_ids=Neo4jGraphRepository._clean_ids(record["related_entity_ids"]),
        )

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
