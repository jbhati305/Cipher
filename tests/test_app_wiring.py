from apps.api.main import create_app


def test_app_registers_local_first_routes() -> None:
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/health" in paths
    assert "/dashboard" in paths
    assert "/api/tasks" in paths
    assert "/api/memory/write" in paths
    assert "/api/voice/alexa/message" in paths
    assert "/api/notion/papers/sync" in paths
