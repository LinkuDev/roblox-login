"""CMS nhe: admin bat/tat banner, modal popup, thong bao he thong khong can deploy.

FE goi `active(placement)` de lay cai dang hien; user co the `dismiss` cai
dismissible -> khong hien lai. Admin CRUD qua cac ham con lai.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.enums import CmsKind
from app.core.errors import BusinessError, NotFoundError
from app.db.models import CmsContent, CmsDismissal
from app.db.repositories import CmsRepository

_EDITABLE = {
    "kind", "placement", "title", "body", "image_url", "link_url", "cta_label",
    "level", "priority", "dismissible", "is_active", "starts_at", "ends_at",
}


class CmsService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = CmsRepository(session)

    # --- public / user -----------------------------------------------------
    def active(
        self,
        placement: str | None = None,
        kind: str | None = None,
        user_id: str | None = None,
    ) -> list[dict]:
        now = datetime.now(UTC)
        items = self.repo.active(now, placement=placement, kind=kind)
        dismissed = self.repo.dismissed_ids(user_id) if user_id else set()
        return [self._view(c) for c in items if c.id not in dismissed]

    def dismiss(self, user_id: str, content_id: str) -> None:
        content = self.repo.get(content_id)
        if not content:
            raise NotFoundError("khong tim thay noi dung")
        if not content.dismissible:
            raise BusinessError("noi dung nay khong the tat")
        if self.repo.dismissal(user_id, content_id) is None:
            self.session.add(CmsDismissal(user_id=user_id, content_id=content_id))

    # --- admin -------------------------------------------------------------
    def list_all(self, limit: int = 200) -> list[dict]:
        return [self._view(c, admin=True) for c in self.repo.all_admin(limit)]

    def get(self, content_id: str) -> dict:
        content = self.repo.get(content_id)
        if not content:
            raise NotFoundError("khong tim thay noi dung")
        return self._view(content, admin=True)

    def create(self, data: dict, created_by: str | None = None) -> dict:
        if str(data.get("kind", CmsKind.BANNER)) not in {str(k) for k in CmsKind}:
            raise BusinessError("kind khong hop le")
        content = CmsContent(created_by=created_by)
        self._assign(content, data)
        self.repo.add(content)
        return self._view(content, admin=True)

    def update(self, content_id: str, data: dict) -> dict:
        content = self.repo.get(content_id)
        if not content:
            raise NotFoundError("khong tim thay noi dung")
        self._assign(content, data)
        self.session.flush()
        return self._view(content, admin=True)

    def delete(self, content_id: str) -> None:
        content = self.repo.get(content_id)
        if not content:
            raise NotFoundError("khong tim thay noi dung")
        self.repo.delete(content)

    # --- noi bo ------------------------------------------------------------
    def _assign(self, content: CmsContent, data: dict) -> None:
        for k, v in data.items():
            if k in _EDITABLE and v is not None:
                setattr(content, k, v)

    @staticmethod
    def _view(c: CmsContent, admin: bool = False) -> dict:
        out = {
            "id": c.id,
            "kind": c.kind,
            "placement": c.placement,
            "title": c.title,
            "body": c.body,
            "image_url": c.image_url,
            "link_url": c.link_url,
            "cta_label": c.cta_label,
            "level": c.level,
            "priority": c.priority,
            "dismissible": c.dismissible,
        }
        if admin:
            out.update(
                is_active=c.is_active,
                starts_at=c.starts_at.isoformat() if c.starts_at else None,
                ends_at=c.ends_at.isoformat() if c.ends_at else None,
                created_at=c.created_at.isoformat(),
            )
        return out
