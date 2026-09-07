from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.db.models import User
from app.modules.orders import OrderService
from app.schemas.order import (
    CreateOrderRequest,
    OrderResponse,
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
