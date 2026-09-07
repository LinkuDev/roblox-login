from __future__ import annotations

from sqlalchemy import select

from app.core.enums import JobStatus
from app.db.models import Record
from app.db.repositories.base import BaseRepository


class RecordRepository(BaseRepository[Record]):
    model = Record

    def by_order(self, order_id: str) -> list[Record]:
        return list(
            self.session.scalars(select(Record).where(Record.order_id == order_id))
        )

    def queued(self, limit: int = 50) -> list[Record]:
        return list(
            self.session.scalars(
                select(Record).where(Record.status == JobStatus.QUEUED).limit(limit)
            )
        )
