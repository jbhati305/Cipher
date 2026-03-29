from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/health")
def healthcheck(request: Request) -> dict:
    settings = request.app.state.settings
    client = request.app.state.neo4j_client
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "neo4j": client.status(),
    }


@router.get("/version")
def version(request: Request) -> dict:
    settings = request.app.state.settings
    return {"app": settings.app_name, "version": settings.app_version}
