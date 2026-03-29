import logging

from neo4j import Driver, GraphDatabase

from core.config import Settings

logger = logging.getLogger(__name__)


class Neo4jGraphClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._driver: Driver | None = None
        self.last_error: str | None = None

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            raise RuntimeError("Neo4j driver is not available.")
        return self._driver

    @property
    def is_ready(self) -> bool:
        return self._driver is not None

    def start(self) -> None:
        self.last_error = None
        if not self._settings.neo4j_configured:
            self.last_error = (
                "Neo4j credentials are missing. Set NEO4J_USERNAME and NEO4J_PASSWORD in .env."
            )
            logger.warning(self.last_error)
            return

        driver = GraphDatabase.driver(
            self._settings.neo4j_uri,
            auth=(self._settings.neo4j_username, self._settings.neo4j_password),
        )

        try:
            if self._settings.neo4j_verify_connectivity:
                driver.verify_connectivity()
        except Exception as exc:
            driver.close()
            self.last_error = str(exc)
            logger.exception("Failed to connect to Neo4j.")
            raise

        self._driver = driver
        logger.info("Connected to Neo4j at %s", self._settings.neo4j_uri)

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            logger.info("Closed Neo4j driver.")
            self._driver = None

    def status(self) -> dict:
        return {
            "configured": self._settings.neo4j_configured,
            "available": self.is_ready,
            "uri": self._settings.neo4j_uri,
            "database": self._settings.neo4j_database,
            "last_error": self.last_error,
        }
