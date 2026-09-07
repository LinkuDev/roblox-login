from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()
_engine = create_engine(
    _settings.db.database_url,
    echo=_settings.db.sql_echo,
    connect_args={"check_same_thread": False}
    if _settings.db.database_url.startswith("sqlite")
    else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Tao bang. Dev only - prod dung alembic."""
    from app.db import models  # noqa: F401  (dang ky models)
    from app.db.base import Base

    Base.metadata.create_all(_engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """Dependency cho FastAPI."""
    with session_scope() as session:
        yield session
