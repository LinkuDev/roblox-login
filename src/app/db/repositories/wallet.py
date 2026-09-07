from __future__ import annotations

from sqlalchemy import select

from app.db.models import PointTransaction, Wallet
from app.db.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    model = Wallet

    def by_user(self, user_id: str) -> Wallet | None:
        return self.session.scalar(select(Wallet).where(Wallet.user_id == user_id))

    def add_transaction(self, tx: PointTransaction) -> PointTransaction:
        self.session.add(tx)
        self.session.flush()
        return tx

    def transactions(self, wallet_id: str, limit: int = 50) -> list[PointTransaction]:
        return list(
            self.session.scalars(
                select(PointTransaction)
                .where(PointTransaction.wallet_id == wallet_id)
                .order_by(PointTransaction.created_at.desc())
                .limit(limit)
            )
        )
