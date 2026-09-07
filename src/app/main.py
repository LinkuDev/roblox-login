"""FastAPI app - tang SaaS. Chay: uvicorn app.main:api"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import install_error_handlers
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    if not get_settings().app.is_prod:
        init_db()   # dev: tu tao bang. prod: dung alembic
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Automation SaaS",
        version="0.1.0",
        debug=settings.app.debug,
        lifespan=lifespan,
    )
    install_error_handlers(app)
    app.include_router(api_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "env": settings.app.env}

    return app


api = create_app()
