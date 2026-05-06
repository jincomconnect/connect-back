from fastapi import FastAPI

from app.api.router import api_router
from app.core.logging import configure_logging
from app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url="/redoc" if settings.app_env != "prod" else None,
    )
    app.include_router(api_router)
    return app


app = create_app()
