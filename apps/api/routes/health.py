from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/health")
def healthcheck(request: Request) -> dict:
    settings = request.app.state.settings
    repository = request.app.state.repository
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "storage": repository.health(),
        "memos": {"configured": bool(settings.memos_base_url), "base_url": settings.memos_base_url},
        "llm": {
            "provider": settings.llm_provider,
            "ollama_base_url": settings.ollama_base_url,
        },
    }


@router.get("/version")
def version(request: Request) -> dict:
    settings = request.app.state.settings
    return {"app": settings.app_name, "version": settings.app_version}
