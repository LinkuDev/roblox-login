"""Nghiep vu don hang: payload user:pass -> validate -> tru diem TRUOC -> sinh
pool record -> day vao queue.

Mo hinh point (moi): tru NGAY khi tao order = so dong hop le * unit_price. Record
fail hien KHONG hoan diem (refund lam sau). Node/report khong dung toi billing.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import JobStatus, OrderStatus
from app.core.errors import BusinessError
from app.db.models import Order, Record
from app.db.repositories import OrderRepository
from app.modules.billing import BillingService
from app.modules.jobs import build_queue
from app.modules.orders.accounts import parse_accounts
from app.services import get_service_spec


class OrderService:
    def __init__(self, session: Session):
        self.session = session
        self.orders = OrderRepository(session)
        self.queue = build_queue()

    def preview(self, service_id: str, accounts_text: str) -> dict:
        """Dry-run cho form: dem so dong hop le / loi + so diem se bi tru.

        Khong tao gi, khong tru gi.
        """
        spec = get_service_spec(service_id)
        creds, errors = parse_accounts(accounts_text)
        valid = len(creds)
        return {
            "service_id": service_id,
            "valid_count": valid,
            "invalid_count": len(errors),
            "unit_price": spec.price_points,
            "total_price": spec.price_points * valid,
            "errors": [e.to_dict() for e in errors],
        }

    def create(self, user_id: str, service_id: str, accounts_text: str, note: str = "") -> Order:
        spec = get_service_spec(service_id)   # raise neu service khong ton tai

        creds, errors = parse_accounts(accounts_text)
        if errors:
            raise BusinessError(
                "payload co dong khong hop le",
                invalid_lines=[e.to_dict() for e in errors],
                valid_count=len(creds),
            )
        if not creds:
            raise BusinessError("khong co dong user:pass hop le nao")

        quantity = len(creds)
        total = spec.price_points * quantity

        order = self.orders.add(
            Order(
                user_id=user_id,
                service_id=service_id,
                status=OrderStatus.PENDING,
                quantity=quantity,
                unit_price=spec.price_points,
                total_price=total,
                note=note,
            )
        )
        self.session.flush()   # lay order.id de gan vao giao dich diem

        # tru diem TRUOC - thieu so du thi raise InsufficientPoints, ca transaction
        # roll back (order chua kip persist) nho session_scope o tang tren.
        if total > 0:
            BillingService(self.session).charge(
                user_id, total, ref_type="order", ref_id=order.id,
                note=f"order {service_id} x{quantity}",
            )

        for cred in creds:
            record = Record(
                order_id=order.id,
                service_id=service_id,
                username=cred.username,
                password=cred.password,
                totp_secret=cred.totp_secret,
                email=cred.email,
                status=JobStatus.QUEUED,
                cost_points=spec.price_points,
            )
            self.session.add(record)
            self.session.flush()
            self.queue.enqueue(record.id, {"record_id": record.id})

        order.status = OrderStatus.PROCESSING
        return order

    def get(self, order_id: str, user_id: str | None = None) -> Order:
        order = self.orders.get(order_id)
        if not order or (user_id and order.user_id != user_id):
            raise BusinessError("khong tim thay don hang")
        return order

    def list_for_user(self, user_id: str) -> list[Order]:
        return self.orders.by_user(user_id)
