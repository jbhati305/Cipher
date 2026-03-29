from pathlib import Path

from core.config import get_settings
from database.neo4j.client import Neo4jGraphClient

SCHEMA_FILES = [
    Path("database/neo4j/constraints.cypher"),
    Path("database/neo4j/schema.cypher"),
]


def main() -> None:
    settings = get_settings()
    client = Neo4jGraphClient(settings)
    client.start()

    if not client.is_ready:
        raise SystemExit(client.last_error or "Neo4j is not ready.")

    try:
        with client.driver.session(database=settings.neo4j_database) as session:
            for path in SCHEMA_FILES:
                for statement in _load_statements(path):
                    session.run(statement).consume()
                print(f"Applied {path}")
    finally:
        client.close()


def _load_statements(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if line.strip() and not line.strip().startswith("//")]
    return [statement.strip() for statement in "\n".join(filtered).split(";") if statement.strip()]


if __name__ == "__main__":
    main()
