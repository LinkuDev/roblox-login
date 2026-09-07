from __future__ import annotations

from sqlalchemy import select

from app.core.enums import JobStatus
from app.db.models import Job
from app.db.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    model = Job

    def pending(self, limit: int = 10) -> list[Job]:
        return list(
            self.session.scalars(
                select(Job).where(Job.status == JobStatus.PENDING).limit(limit)
            )
        )
