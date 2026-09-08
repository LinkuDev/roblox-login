from __future__ import annotations

from sqlalchemy import func, or_, select

from app.db.models import Notification, NotificationRead
from app.db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    def _visible_filter(self, user_id: str):
        """Thong bao user duoc thay: rieng minh HOAC broadcast (user_id NULL)."""
        return or_(Notification.user_id == user_id, Notification.user_id.is_(None))

    def _read_ids_subq(self, user_id: str):
        return select(NotificationRead.notification_id).where(
            NotificationRead.user_id == user_id
        )

    def for_user(
        self, user_id: str, unread_only: bool = False, limit: int = 50, offset: int = 0
    ) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(self._visible_filter(user_id))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if unread_only:
            stmt = stmt.where(Notification.id.not_in(self._read_ids_subq(user_id)))
        return list(self.session.scalars(stmt))

    def unread_count(self, user_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                self._visible_filter(user_id),
                Notification.id.not_in(self._read_ids_subq(user_id)),
            )
        )
        return int(self.session.scalar(stmt) or 0)

    def read_marker(self, user_id: str, notification_id: str) -> NotificationRead | None:
        return self.session.scalar(
            select(NotificationRead).where(
                NotificationRead.user_id == user_id,
                NotificationRead.notification_id == notification_id,
            )
        )

    def unread_visible_ids(self, user_id: str) -> list[str]:
        stmt = (
            select(Notification.id)
            .where(
                self._visible_filter(user_id),
                Notification.id.not_in(self._read_ids_subq(user_id)),
            )
        )
        return list(self.session.scalars(stmt))
