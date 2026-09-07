from __future__ import annotations

from sqlalchemy import select

from app.db.models import Order, OrderItem
from app.db.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    model = Order

    def by_user(self, user_id: str, limit: int = 50) -> list[Order]:
        return list(
            self.session.scalars(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(limit)
            )
        )

    def add_item(self, item: OrderItem) -> OrderItem:
        self.session.add(item)
        self.session.flush()
        return item
