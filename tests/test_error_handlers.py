from fastapi.testclient import TestClient

from apps.api.main import create_app
from core.config import get_settings


def test_unhandled_exceptions_return_json_500_response(monkeypatch) -> None:
    monkeypatch.setenv("CIPHER_DEBUG", "false")
    get_settings.cache_clear()
    app = create_app()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    get_settings.cache_clear()
