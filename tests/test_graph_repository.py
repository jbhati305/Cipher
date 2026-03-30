from datetime import UTC, datetime

from neo4j.time import DateTime

from core.repositories.graph_repository import Neo4jGraphRepository


def test_normalize_properties_converts_neo4j_datetime_to_python_datetime() -> None:
    native_now = datetime.now(UTC)
    neo4j_now = DateTime.from_native(native_now)

    result = Neo4jGraphRepository._normalize_properties(
        {
            "created_at": neo4j_now,
            "nested": {"updated_at": neo4j_now},
            "values": [neo4j_now],
        }
    )

    assert result["created_at"] == native_now
    assert isinstance(result["created_at"], datetime)
    assert result["nested"]["updated_at"] == native_now
    assert result["values"][0] == native_now


def test_build_entity_code_uses_prefix_period_and_zero_padded_sequence() -> None:
    created_at = datetime(2026, 3, 30, 6, 0, tzinfo=UTC)

    result = Neo4jGraphRepository._build_entity_code("PRJ", created_at, 42)

    assert result == "PRJ-2603-000042"
