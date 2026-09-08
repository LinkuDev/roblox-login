from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()
_is_sqlite = _settings.db.database_url.startswith("sqlite")
_engine = create_engine(
    _settings.db.database_url,
    echo=_settings.db.sql_echo,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
)

# SQLite + NHIEU node claim dong thoi: bat WAL (doc song song + 1 writer) va
# busy_timeout (writer CHO khi bi khoa thay vi loi ngay) -> claim khong trung, khong
# vo "database is locked". (Scale lon that su -> chuyen Postgres + SKIP LOCKED.)
if _is_sqlite:

    @event.listens_for(_engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _rec):  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=8000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()


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
