"""API pool phan tan.

- POST /pool/claim  (ADMIN): node lay 1 record. Key node = key cua tai khoan ADMIN
  (noi bo). Khach (role=user) KHONG duoc claim/report.
- POST /pool/report (ADMIN): bao ket qua.
- GET  /pool/records (user): khach xem record CUA MINH; admin xem tat ca.
- GET  /pool/stats   (user): dem theo status (scoped nhu tren).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, require_admin
from app.core.enums import UserRole
from app.db.models import User
from app.modules.pool import PoolService

router = APIRouter(prefix="/pool", tags=["pool"])


class ClaimBody(BaseModel):
    node_id: str = ""
    ttl_seconds: int = 300


class ReportBody(BaseModel):
    record_id: str
    result: dict
    node_id: str = ""


class RecordView(BaseModel):
    id: str
    order_id: str
    username: str
    status: str
    attempt: int
    node_id: str
    error_code: str
    reason: str

    class Config:
        from_attributes = True


@router.post("/claim")
def claim(
    body: ClaimBody,
    _admin: User = Depends(require_admin),   # chi ADMIN (node dung key admin noi bo)
    session: Session = Depends(db_session),
):
    """Node lay 1 record (atomic). 204 No Content neu pool rong."""
    claimed = PoolService(session).claim_next(body.node_id or "node", body.ttl_seconds)
    if claimed is None:
        return Response(status_code=204)
    return claimed


@router.post("/report")
def report(
    body: ReportBody,
    _admin: User = Depends(require_admin),
    session: Session = Depends(db_session),
):
    return PoolService(session).report(body.record_id, body.result, body.node_id)


def _scope(user: User) -> str | None:
    """None = admin xem tat ca; nguoc lai chi record cua chinh user."""
    return None if user.role == UserRole.ADMIN else user.id


@router.get("/records", response_model=list[RecordView])
def records(
    order_id: str | None = None,
    status: str | None = None,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    return PoolService(session).list_records(
        order_id=order_id, status=status, user_id=_scope(user)
    )


@router.get("/stats")
def stats(user: User = Depends(current_user), session: Session = Depends(db_session)):
    return PoolService(session).stats(user_id=_scope(user))
