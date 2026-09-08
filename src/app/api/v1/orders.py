from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.db.models import User
from app.modules.orders import OrderService
from app.schemas.order import (
    CreateOrderRequest,
    OrderResponse,
    RecordDetail,
    ValidateOrderResponse,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/validate", response_model=ValidateOrderResponse)
def validate_order(
    body: CreateOrderRequest,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    """Dry-run: form goi truoc khi submit de bao so diem se tru + dong loi.

    Khong tao order, khong tru diem.
    """
    return OrderService(session).preview(body.service_id, body.accounts)


@router.post("", response_model=OrderResponse)
def create_order(
    body: CreateOrderRequest,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    return OrderService(session).create(user.id, body.service_id, body.accounts, body.note)


@router.get("", response_model=list[OrderResponse])
def my_orders(user: User = Depends(current_user), session: Session = Depends(db_session)):
    return OrderService(session).list_for_user(user.id)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    return OrderService(session).get(order_id, user.id)


@router.get("/{order_id}/records", response_model=list[RecordDetail])
def order_records(
    order_id: str,
    status: str | None = None,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    """Records cua 1 don (kem cookie/ket qua). Chi chu don xem duoc."""
    return OrderService(session).records(order_id, user.id, status)


@router.get("/{order_id}/export", response_class=PlainTextResponse)
def export_order(
    order_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    """Xuat cookie cac record thanh cong dang text (user:cookie moi dong)."""
    return OrderService(session).export(order_id, user.id)
