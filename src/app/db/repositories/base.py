from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

M = TypeVar("M", bound=Base)


class BaseRepository(Generic[M]):
    model: type[M]

    def __init__(self, session: Session):
        self.session = session

    def get(self, id_: str) -> M | None:
        return self.session.get(self.model, id_)

    def list(self, limit: int = 100, offset: int = 0) -> list[M]:
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.scalars(stmt))

    def add(self, obj: M) -> M:
        self.session.add(obj)
        self.session.flush()
        return obj

    def delete(self, obj: M) -> None:
        self.session.delete(obj)
