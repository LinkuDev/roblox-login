"""FastAPI app - tang SaaS. Chay: uvicorn app.main:api"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.errors import install_error_handlers
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import init_db
from app.web_page import WEB_PAGE


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

    # CORS: FE Next.js (repo rieng) goi API. Auth qua header Bearer/X-API-Key (khong
    # dung cookie) -> allow_credentials=False, cho phep dung "*" khi dev.
    origins = settings.app.cors_origin_list()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/", response_class=HTMLResponse)
    def web():
        """Trang SaaS: login/register, tao order, xem pool."""
        return WEB_PAGE

    @app.get("/health")
    def health():
        return {"status": "ok", "env": settings.app.env}

    return app


api = create_app()
