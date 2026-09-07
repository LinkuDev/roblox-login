from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_session
from app.db.models import User
from app.modules.orders import OrderService
from app.schemas.order import CreateOrderRequest, OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
def create_order(
    body: CreateOrderRequest,
    user: User = Depends(current_user),
    session: Session = Depends(db_session),
):
    order = OrderService(session).create(
        user.id, body.service_id, [i.model_dump() for i in body.inputs], body.note
    )
    return order


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
