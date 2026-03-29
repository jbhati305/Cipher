from core.config import get_settings
from database.neo4j.client import Neo4jGraphClient


def main() -> None:
    settings = get_settings()
    client = Neo4jGraphClient(settings)
    client.start()

    if not client.is_ready:
        raise SystemExit(client.last_error or "Neo4j is not ready.")

    try:
        with client.driver.session(database=settings.neo4j_database) as session:
            record = session.run("RETURN 1 AS ok, datetime() AS server_time").single()
            print(
                {
                    "ok": record["ok"],
                    "server_time": str(record["server_time"]),
                    "uri": settings.neo4j_uri,
                    "database": settings.neo4j_database,
                }
            )
    finally:
        client.close()


if __name__ == "__main__":
    main()
