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

        from app.core.enums import NotificationLevel
        from app.modules.notifications import NotificationService

        NotificationService(self.session).notify(
            user_id,
            title="Da tao don hang",
            body=f"Don {service_id} x{quantity} - da tru {total} diem, dang xu ly.",
            level=NotificationLevel.INFO,
            ref_type="order",
            ref_id=order.id,
        )
        return order

    def get(self, order_id: str, user_id: str | None = None) -> Order:
        order = self.orders.get(order_id)
        if not order or (user_id and order.user_id != user_id):
            raise BusinessError("khong tim thay don hang")
        return order

    def list_for_user(self, user_id: str) -> list[Order]:
        return self.orders.by_user(user_id)

    def records(
        self, order_id: str, user_id: str | None = None, status: str | None = None
    ) -> list[dict]:
        """Records cua 1 order (co check chu so huu). Kem cookie/ket qua cho chu don."""
        from app.db.repositories import RecordRepository

        self.get(order_id, user_id)   # raise neu khong phai don cua user
        rows = RecordRepository(self.session).by_order(order_id)
        if status:
            rows = [r for r in rows if str(r.status) == status]
        return [self._record_view(r) for r in rows]

    def export(self, order_id: str, user_id: str | None = None) -> str:
        """Xuat cookie cac record THANH CONG dang text (moi dong 1 cookie).

        Day la "san pham" khach mua: gia tri .ROBLOSECURITY / session tra ve.
        """
        import json

        from app.core.enums import JobStatus

        lines: list[str] = []
        for r in self.records(order_id, user_id, status=str(JobStatus.SUCCESS)):
            cookie = ""
            raw = r.get("cookies") or ""
            if raw:
                try:
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        cookie = data.get(".ROBLOSECURITY") or data.get("cookie") or raw
                    else:
                        cookie = raw
                except (ValueError, TypeError):
                    cookie = raw
            lines.append(f"{r['username']}:{cookie}" if cookie else r["username"])
        return "\n".join(lines)

    @staticmethod
    def _record_view(r) -> dict:
        return {
            "id": r.id,
            "order_id": r.order_id,
            "username": r.username,
            "status": r.status,
            "attempt": r.attempt,
            "error_code": r.error_code,
            "reason": r.reason,
            "cookies": r.cookies,
            "duration": r.duration,
            "created_at": r.created_at.isoformat(),
        }
