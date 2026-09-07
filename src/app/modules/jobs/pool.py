"""Duong noi giua tang SaaS (pool + DB) va nhan automation (flow).

Ba pha, chinh la ranh gioi node <-> SaaS sau nay:

  claim_input(record_id)   -> doc record, danh dau RUNNING, tra Credential   [SaaS/DB]
  run_service(...)         -> chay flow, tra RunResult                        [NODE]
  report_result(record_id) -> ghi status + cookies + reason len record        [SaaS/DB]

`process_record` gan ca ba lai in-process cho worker co-located (dev/1 may). Node
remote sau nay se goi claim/report qua transport, con run_service chay tai cho.
Billing KHONG nam o day - da tru truoc luc tao order.
"""

from __future__ import annotations

import json

from app.automation.result import RunResult
from app.automation.runner import run_service
from app.core.enums import JobStatus, OrderStatus
from app.core.logging import get_logger
from app.db.repositories import OrderRepository, RecordRepository
from app.db.session import session_scope
from app.domain.models import Credential

log = get_logger("pool")


def claim_input(record_id: str) -> tuple[Credential, str] | None:
    """Nhan input cua record + danh dau dang chay. None neu bo qua (khong ton tai
    hoac da xong/dang chay)."""
    with session_scope() as session:
        record = RecordRepository(session).get(record_id)
        if not record:
            log.warning("record_not_found", record_id=record_id)
            return None
        if record.status in (JobStatus.SUCCESS, JobStatus.RUNNING):
            log.info("record_skip", record_id=record_id, status=str(record.status))
            return None

        record.status = JobStatus.RUNNING
        record.attempt += 1
        credential = Credential(
            username=record.username,
            password=record.password,
            totp_secret=record.totp_secret,
            email=record.email,
        )
        return credential, record.service_id


def report_result(record_id: str, result: RunResult) -> dict:
    """Ghi ket qua len record + cap nhat dem cua order. Khong dung toi diem."""
    with session_scope() as session:
        record = RecordRepository(session).get(record_id)
        if not record:
            return {"ok": False, "error": "record_not_found"}
        order = OrderRepository(session).get(record.order_id)

        record.result_json = json.dumps(result.to_dict(), ensure_ascii=False)
        record.duration = result.duration

        if result.success:
            record.status = JobStatus.SUCCESS
            record.error_code = ""
            record.reason = ""
            session_data = result.data.get("session") or {}
            cookies = session_data.get("cookies") or result.data.get("cookies") or {}
            record.cookies = json.dumps(cookies, ensure_ascii=False)
            if order:
                order.completed_count += 1
        else:
            record.status = JobStatus.FAILED
            record.error_code = result.error_code or "failed"
            record.reason = result.error_message or ""
            if order:
                order.failed_count += 1

        if order:
            _sync_order_status(order)
        return {"ok": result.success, "status": str(record.status)}


def process_record(record_id: str) -> dict:
    """Chay 1 record den cung (local worker). Idempotent theo trang thai record."""
    claimed = claim_input(record_id)
    if claimed is None:
        return {"ok": True, "skipped": True}
    credential, service_id = claimed
    result = run_service(service_id, credential, job_id=record_id)
    return report_result(record_id, result)


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
