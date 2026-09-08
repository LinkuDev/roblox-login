from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.db.models import User
from app.modules.notifications import NotificationService
from app.schemas.notification import NotificationView, UnreadCountResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationView])
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    return NotificationService(session).list(user.id, unread_only, limit, offset)


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(user: User = Depends(current_user), session: Session = Depends(db_session)):
    return UnreadCountResponse(unread=NotificationService(session).unread_count(user.id))


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    NotificationService(session).mark_read(user.id, notification_id)
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(user: User = Depends(current_user), session: Session = Depends(db_session)):
    n = NotificationService(session).mark_all_read(user.id)
    return {"ok": True, "marked": n}
