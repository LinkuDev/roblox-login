"""Cau noi giua tang SaaS va nhan automation.

Nhan 1 job_id -> doc order item -> chay service -> cap nhat DB + tinh diem.
Day la ham worker goi. Tach khoi runner de runner van chay doc lap (CLI).
"""

from __future__ import annotations

import json

from app.automation.runner import run_service
from app.core.enums import JobStatus, OrderStatus
from app.core.logging import get_logger
from app.db.models import Job, OrderItem
from app.db.repositories import JobRepository, OrderRepository
from app.db.session import session_scope
from app.domain.models import Credential
from app.modules.billing import BillingService

log = get_logger("executor")


def execute_job(job_id: str) -> dict:
    """Chay 1 job den cung, cap nhat trang thai. Idempotent theo trang thai."""
    with session_scope() as session:
        job = JobRepository(session).get(job_id)
        if not job:
            log.warning("job_not_found", job_id=job_id)
            return {"ok": False, "error": "job_not_found"}
        if job.status in (JobStatus.SUCCESS, JobStatus.RUNNING):
            return {"ok": True, "skipped": True, "status": str(job.status)}

        item = session.get(OrderItem, job.order_item_id)
        order = OrderRepository(session).get(item.order_id) if item else None
        if not item or not order:
            job.status = JobStatus.FAILED
            job.error_code = "missing_order"
            return {"ok": False, "error": "missing_order"}

        job.status = JobStatus.RUNNING
        job.attempts += 1
        credential = Credential(**json.loads(item.input_ref))
        session.flush()
        service_id = job.service_id
        user_id = order.user_id
        unit_price = order.unit_price

    # chay ngoai transaction DB (chay lau, khong giu ket noi)
    result = run_service(service_id, credential, job_id=job_id)

    with session_scope() as session:
        job = JobRepository(session).get(job_id)
        item = session.get(OrderItem, job.order_item_id)
        order = OrderRepository(session).get(item.order_id)
        billing = BillingService(session)

        job.result_json = json.dumps(result.to_dict(), ensure_ascii=False)
        job.duration = result.duration
        job.status = JobStatus.SUCCESS if result.success else JobStatus.FAILED
        item.status = job.status

        if result.success:
            job.cost_points = unit_price
            order.completed_count += 1
            if unit_price:
                billing.charge(
                    user_id, unit_price, ref_type="order", ref_id=order.id,
                    note=f"job {job_id} {service_id}",
                )
        else:
            job.error_code = result.error_code or "failed"
            order.failed_count += 1

        _sync_order_status(order)
        return {"ok": result.success, "status": str(job.status)}


def _sync_order_status(order) -> None:
    done = order.completed_count + order.failed_count
    if done < order.quantity:
        order.status = OrderStatus.PROCESSING
    elif order.failed_count == 0:
        order.status = OrderStatus.COMPLETED
    elif order.completed_count == 0:
        order.status = OrderStatus.FAILED
    else:
        order.status = OrderStatus.PARTIAL
