from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, or_, select

from app.db.models import CmsContent, CmsDismissal
from app.db.repositories.base import BaseRepository


class CmsRepository(BaseRepository[CmsContent]):
    model = CmsContent

    def all_admin(self, limit: int = 200) -> list[CmsContent]:
        return list(
            self.session.scalars(
                select(CmsContent).order_by(CmsContent.created_at.desc()).limit(limit)
            )
        )

    def active(
        self, now: datetime, placement: str | None = None, kind: str | None = None
    ) -> list[CmsContent]:
        """Dang bat + trong cua so thoi gian (starts/ends NULL = khong gioi han)."""
        stmt = (
            select(CmsContent)
            .where(
                CmsContent.is_active.is_(True),
                or_(CmsContent.starts_at.is_(None), CmsContent.starts_at <= now),
                or_(CmsContent.ends_at.is_(None), CmsContent.ends_at >= now),
            )
            .order_by(CmsContent.priority.desc(), CmsContent.created_at.desc())
        )
        if placement:
            stmt = stmt.where(CmsContent.placement == placement)
        if kind:
            stmt = stmt.where(CmsContent.kind == kind)
        return list(self.session.scalars(stmt))

    def dismissed_ids(self, user_id: str) -> set[str]:
        rows = self.session.scalars(
            select(CmsDismissal.content_id).where(CmsDismissal.user_id == user_id)
        )
        return set(rows)

    def dismissal(self, user_id: str, content_id: str) -> CmsDismissal | None:
        return self.session.scalar(
            select(CmsDismissal).where(
                and_(
                    CmsDismissal.user_id == user_id,
                    CmsDismissal.content_id == content_id,
                )
            )
        )
