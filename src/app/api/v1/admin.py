"""Endpoint chi ADMIN: quan ly CMS (banner/modal), confirm lenh nap, gui thong bao.

Tach rieng khoi router khach de ranh gioi quyen ro rang (require_admin toan router).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, require_admin
from app.db.models import User
from app.modules.cms import CmsService
from app.modules.notifications import NotificationService
from app.modules.payments import PaymentService
from app.schemas.cms import CmsCreateRequest, CmsUpdateRequest
from app.schemas.notification import BroadcastRequest
from app.schemas.payment import DepositConfirmRequest

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# --- CMS ------------------------------------------------------------------
@router.get("/cms")
def list_cms(session: Session = Depends(db_session)):
    return CmsService(session).list_all()


@router.post("/cms")
def create_cms(
    body: CmsCreateRequest,
    admin: User = Depends(require_admin),
    session: Session = Depends(db_session),
):
    return CmsService(session).create(body.model_dump(), created_by=admin.id)


@router.get("/cms/{content_id}")
def get_cms(content_id: str, session: Session = Depends(db_session)):
    return CmsService(session).get(content_id)


@router.patch("/cms/{content_id}")
def update_cms(
    content_id: str, body: CmsUpdateRequest, session: Session = Depends(db_session)
):
    return CmsService(session).update(content_id, body.model_dump(exclude_unset=True))


@router.delete("/cms/{content_id}")
def delete_cms(content_id: str, session: Session = Depends(db_session)):
    CmsService(session).delete(content_id)
    return {"ok": True}


# --- Notification broadcast -----------------------------------------------
@router.post("/notifications")
def broadcast(body: BroadcastRequest, session: Session = Depends(db_session)):
    n = NotificationService(session).notify(
        user_id=body.user_id,
        title=body.title,
        body=body.body,
        level=body.level,
        link_url=body.link_url,
    )
    return {"ok": True, "id": n.id, "broadcast": body.user_id is None}


# --- Deposits (crypto) -----------------------------------------------------
@router.post("/deposits/{deposit_id}/confirm")
def confirm_deposit(
    deposit_id: str,
    body: DepositConfirmRequest,
    session: Session = Depends(db_session),
):
    """Confirm tay 1 lenh nap (provider manual / tranh chap) -> cong diem 1 lan."""
    return PaymentService(session).admin_confirm(deposit_id, body.tx_hash)
