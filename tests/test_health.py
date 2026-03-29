from fastapi.testclient import TestClient

from apps.api.main import create_app


def test_health_endpoint_is_available() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "neo4j" in payload
