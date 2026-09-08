"""Thong bao trong app: tao (rieng user hoac broadcast), liet ke, dem chua doc,
danh dau da doc. Cac module khac goi `notify(...)` de bao su kien cho user."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import NotificationLevel
from app.core.errors import NotFoundError, PermissionDenied
from app.db.models import Notification, NotificationRead
from app.db.repositories import NotificationRepository


class NotificationService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = NotificationRepository(session)

    # --- tao ---------------------------------------------------------------
    def notify(
        self,
        user_id: str | None,
        title: str,
        body: str = "",
        level: NotificationLevel | str = NotificationLevel.INFO,
        ref_type: str = "",
        ref_id: str = "",
        link_url: str = "",
    ) -> Notification:
        """Tao 1 thong bao. user_id=None -> broadcast (moi user thay)."""
        notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            level=str(level),
            ref_type=ref_type,
            ref_id=ref_id,
            link_url=link_url,
        )
        return self.repo.add(notif)

    # --- doc ---------------------------------------------------------------
    def list(
        self, user_id: str, unread_only: bool = False, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        from sqlalchemy import select

        read_ids = set(
            self.session.scalars(
                select(NotificationRead.notification_id).where(
                    NotificationRead.user_id == user_id
                )
            )
        )
        items = self.repo.for_user(user_id, unread_only, limit, offset)
        return [self._view(n, n.id not in read_ids) for n in items]

    def unread_count(self, user_id: str) -> int:
        return self.repo.unread_count(user_id)

    # --- danh dau doc ------------------------------------------------------
    def mark_read(self, user_id: str, notification_id: str) -> None:
        notif = self.repo.get(notification_id)
        if not notif:
            raise NotFoundError("khong tim thay thong bao")
        # chi cho danh dau cai minh duoc thay (rieng minh hoac broadcast)
        if notif.user_id is not None and notif.user_id != user_id:
            raise PermissionDenied("khong phai thong bao cua ban")
        if self.repo.read_marker(user_id, notification_id) is None:
            self.session.add(
                NotificationRead(user_id=user_id, notification_id=notification_id)
            )

    def mark_all_read(self, user_id: str) -> int:
        ids = self.repo.unread_visible_ids(user_id)
        for nid in ids:
            self.session.add(NotificationRead(user_id=user_id, notification_id=nid))
        return len(ids)

    # --- noi bo ------------------------------------------------------------
    @staticmethod
    def _view(n: Notification, unread: bool) -> dict:
        return {
            "id": n.id,
            "level": n.level,
            "title": n.title,
            "body": n.body,
            "link_url": n.link_url,
            "ref_type": n.ref_type,
            "ref_id": n.ref_id,
            "is_broadcast": n.user_id is None,
            "unread": unread,
            "created_at": n.created_at.isoformat(),
        }
