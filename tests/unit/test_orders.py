"""Phase 1: tao order tu payload user:pass -> validate -> tru diem truoc -> pool.

Chi test tang SaaS (order/billing/record), khong dung browser/flow.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401  - dang ky bang len Base.metadata
from app.core.enums import JobStatus, OrderStatus
from app.core.errors import BusinessError, InsufficientPoints
from app.db.base import Base
from app.db.models import Order, Record
from app.modules.billing import BillingService
from app.modules.orders import OrderService

USER = "user-1"


@pytest.fixture()
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def _topup(session, amount: int) -> None:
    BillingService(session).topup(USER, amount, note="test")


def test_create_charges_upfront_and_builds_pool(session):
    _topup(session, 100)
    order = OrderService(session).create(USER, "roblox.login", "a:p1\nb:p2\nc:p3\n")

    assert order.quantity == 3
    assert order.unit_price == 1
    assert order.total_price == 3
    assert order.status == OrderStatus.PROCESSING

    records = session.query(Record).filter_by(order_id=order.id).all()
    assert len(records) == 3
    assert {r.username for r in records} == {"a", "b", "c"}
    assert all(r.status == JobStatus.QUEUED for r in records)

    # diem bi tru NGAY luc tao (3 record * 1 diem)
    assert BillingService(session).balance(USER) == 97


def test_invalid_lines_reject_whole_order(session):
    _topup(session, 100)
    with pytest.raises(BusinessError) as exc:
        OrderService(session).create(USER, "roblox.login", "a:p1\nbadline\nc:p3\n")

    assert "invalid_lines" in exc.value.context
    assert exc.value.context["invalid_lines"][0]["line"] == 2
    # khong tao order, khong tru diem
    assert session.query(Order).count() == 0
    assert BillingService(session).balance(USER) == 100


def test_insufficient_balance_blocks_order(session):
    _topup(session, 2)
    session.commit()  # topup la giao dich rieng, da commit truoc
    with pytest.raises(InsufficientPoints):
        OrderService(session).create(USER, "roblox.login", "a:1\nb:2\nc:3\nd:4\ne:5\n")
    session.rollback()  # dung nhu session_scope o tang API

    assert session.query(Order).count() == 0
    assert BillingService(session).balance(USER) == 2


def test_empty_payload_rejected(session):
    _topup(session, 10)
    with pytest.raises(BusinessError):
        OrderService(session).create(USER, "roblox.login", "\n# chi comment\n   \n")


def test_preview_does_not_charge(session):
    _topup(session, 10)
    out = OrderService(session).preview("roblox.login", "a:1\nbadline\nb:2\n")

    assert out["valid_count"] == 2
    assert out["invalid_count"] == 1
    assert out["total_price"] == 2
    assert out["errors"][0]["line"] == 2
    # khong tru gi
    assert BillingService(session).balance(USER) == 10
    assert session.query(Order).count() == 0
