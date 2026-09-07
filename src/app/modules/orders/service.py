"""Nghiep vu don hang: tao don tu input -> sinh order item + job -> day vao queue.

Mo hinh point: khong tru truoc; tru khi tung job THANH CONG (trong executor).
Muon tru-truoc-hoan-sau thi doi o day, cac tang khac khong bi anh huong.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.enums import JobStatus, OrderStatus
from app.core.errors import BusinessError
from app.db.models import Job, Order, OrderItem
from app.db.repositories import OrderRepository
from app.domain.models import Credential
from app.modules.jobs import build_queue
from app.services import get_service_spec


class OrderService:
    def __init__(self, session: Session):
        self.session = session
        self.orders = OrderRepository(session)
        self.queue = build_queue()

    def create(self, user_id: str, service_id: str, inputs: list[dict], note: str = "") -> Order:
        spec = get_service_spec(service_id)   # raise neu service khong ton tai
        if not inputs:
            raise BusinessError("don hang khong co input nao")

        order = self.orders.add(
            Order(
                user_id=user_id,
                service_id=service_id,
                status=OrderStatus.PENDING,
                quantity=len(inputs),
                unit_price=spec.price_points,
                total_price=spec.price_points * len(inputs),
                note=note,
            )
        )

        for raw in inputs:
            cred = self._normalize_input(raw)
            item = self.orders.add_item(
                OrderItem(
                    order_id=order.id,
                    input_ref=json.dumps(cred.__dict__, ensure_ascii=False),
                    status="pending",
                )
            )
            job = Job(order_item_id=item.id, service_id=service_id, status=JobStatus.QUEUED)
            self.session.add(job)
            self.session.flush()
            self.queue.enqueue(job.id, {"job_id": job.id})

        return order

    def get(self, order_id: str, user_id: str | None = None) -> Order:
        order = self.orders.get(order_id)
        if not order or (user_id and order.user_id != user_id):
            raise BusinessError("khong tim thay don hang")
        return order

    def list_for_user(self, user_id: str) -> list[Order]:
        return self.orders.by_user(user_id)

    @staticmethod
    def _normalize_input(raw: dict) -> Credential:
        if "username" not in raw or "password" not in raw:
            raise BusinessError("moi input can username va password")
        return Credential(
            username=raw["username"],
            password=raw["password"],
            totp_secret=raw.get("totp_secret"),
            email=raw.get("email"),
            meta=raw.get("meta", {}),
        )
