from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, optional_user
from app.db.models import User
from app.modules.cms import CmsService
from app.schemas.cms import CmsView

router = APIRouter(prefix="/cms", tags=["cms"])


@router.get("/active", response_model=list[CmsView])
def active_content(
    placement: str | None = None,
    kind: str | None = None,
    user: User | None = Depends(optional_user),
    session: Session = Depends(db_session),
):
    """Noi dung dang hien (banner/modal/announcement). Public; neu co token thi loc
    bo cai user da tat (dismiss)."""
    return CmsService(session).active(
        placement=placement, kind=kind, user_id=user.id if user else None
    )


@router.post("/{content_id}/dismiss")
def dismiss(
    content_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    """User tat 1 noi dung dismissible -> khong hien lai."""
    CmsService(session).dismiss(user.id, content_id)
    return {"ok": True}
