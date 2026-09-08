from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session, require_admin
from app.core.config import get_settings
from app.db.models import User
from app.modules.billing import BillingService
from app.modules.payments import PaymentService
from app.schemas.billing import BalanceResponse, TopupRequest, TransactionResponse
from app.schemas.payment import (
    CryptoConfigResponse,
    DepositCreateRequest,
    DepositView,
)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/balance", response_model=BalanceResponse)
def balance(user: User = Depends(current_user), session: Session = Depends(db_session)):
    return BalanceResponse(balance=BillingService(session).balance(user.id))


@router.get("/transactions", response_model=list[TransactionResponse])
def transactions(
    limit: int = 50,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    """So cai diem cua chinh user (topup/deposit/spend/refund/bonus)."""
    billing = BillingService(session)
    wallet = billing.ensure_wallet(user.id)
    return billing.wallets.transactions(wallet.id, limit)


@router.post("/topup", response_model=BalanceResponse)
def topup(
    body: TopupRequest,
    _admin: User = Depends(require_admin),   # admin cong tay; nap tu dong dung /deposits
    session: Session = Depends(db_session),
):
    new_balance = BillingService(session).topup(body.user_id, body.amount, body.note)
    return BalanceResponse(balance=new_balance)


# --- Nap diem qua crypto ---------------------------------------------------
@router.get("/crypto-config", response_model=CryptoConfigResponse)
def crypto_config():
    """Cau hinh nap cho FE: bat/tat, ty gia, currency ho tro, nap toi thieu."""
    c = get_settings().crypto
    return CryptoConfigResponse(
        enabled=c.enabled,
        provider=c.provider,
        min_points=c.min_points,
        points_per_usd=c.points_per_usd,
        currencies=c.currency_list(),
    )


@router.post("/deposits", response_model=DepositView)
def create_deposit(
    body: DepositCreateRequest,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    """Tao lenh nap crypto -> tra dia chi/invoice de user chuyen tien."""
    return PaymentService(session).create_deposit(user.id, body.amount_points, body.currency)


@router.get("/deposits", response_model=list[DepositView])
def list_deposits(user: User = Depends(current_user), session: Session = Depends(db_session)):
    return PaymentService(session).list_for_user(user.id)


@router.get("/deposits/{deposit_id}", response_model=DepositView)
def get_deposit(
    deposit_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    return PaymentService(session).get(deposit_id, user.id)


@router.post("/deposits/{deposit_id}/cancel", response_model=DepositView)
def cancel_deposit(
    deposit_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    return PaymentService(session).cancel(deposit_id, user.id)


@router.post("/deposits/webhook")
async def deposit_webhook(request: Request, session: Session = Depends(db_session)):
    """Callback provider goi ve (khong auth - xac thuc bang chu ky IPN trong provider).
    Idempotent: da CONFIRMED thi khong cong lai."""
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    return PaymentService(session).handle_webhook(headers, body)
