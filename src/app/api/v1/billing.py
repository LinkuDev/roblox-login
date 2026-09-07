from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, require_admin
from app.db.models import User
from app.modules.billing import BillingService
from app.schemas.billing import BalanceResponse, TopupRequest

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/balance", response_model=BalanceResponse)
def balance(user: User = Depends(current_user), session: Session = Depends(db_session)):
    return BalanceResponse(balance=BillingService(session).balance(user.id))


@router.post("/topup", response_model=BalanceResponse)
def topup(
    body: TopupRequest,
    _admin: User = Depends(require_admin),   # tam thoi admin cong tay; sau noi cong thanh toan
    session: Session = Depends(db_session),
):
    new_balance = BillingService(session).topup(body.user_id, body.amount, body.note)
    return BalanceResponse(balance=new_balance)
