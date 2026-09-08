from __future__ import annotations

from sqlalchemy import select

from app.db.models import Deposit
from app.db.repositories.base import BaseRepository


class DepositRepository(BaseRepository[Deposit]):
    model = Deposit

    def by_user(self, user_id: str, limit: int = 50) -> list[Deposit]:
        return list(
            self.session.scalars(
                select(Deposit)
                .where(Deposit.user_id == user_id)
                .order_by(Deposit.created_at.desc())
                .limit(limit)
            )
        )

    def by_external_id(self, external_id: str) -> Deposit | None:
        if not external_id:
            return None
        return self.session.scalar(
            select(Deposit).where(Deposit.external_id == external_id)
        )
