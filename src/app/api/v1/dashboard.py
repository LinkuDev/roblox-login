from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, require_admin
from app.db.models import User
from app.modules.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def my_dashboard(user: User = Depends(current_user), session: Session = Depends(db_session)):
    """Tong hop so lieu cua chinh user: balance, order/record theo status, chi tieu,
    ty le thanh cong, so thong bao chua doc, hoat dong gan day."""
    return DashboardService(session).for_user(user.id)


@router.get("/admin")
def admin_dashboard(
    _admin: User = Depends(require_admin), session: Session = Depends(db_session)
):
    """So lieu toan he thong (chi admin)."""
    return DashboardService(session).admin_overview()
