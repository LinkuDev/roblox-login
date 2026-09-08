"""Pool phan tan: node claim record -> chay -> report.

CLAIM ATOMIC (chong 2 node lay trung 1 record): 1 cau UPDATE nguyen tu chon +
danh dau 1 record dang `queued` (hoac `running` da het han TTL -> reclaim node chet).
SQLite tuan tu hoa ghi -> khong trung; Postgres co the them SKIP LOCKED sau.

REPORT: success -> ghi cookie. failed -> phan loai:
  - loi login (terminal) -> FAILED.
  - loi ha tang & con luot -> tra lai QUEUED (attempt da tang) de node khac claim.
Billing KHONG dung o day (da tru truoc luc tao order).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.enums import JobStatus, OrderStatus
from app.core.logging import get_logger
from app.db.models import Order, Record
from app.db.repositories import OrderRepository, RecordRepository
from app.domain.models import Credential
from app.modules.pool.policy import RETRYABLE_MAX_ATTEMPTS, is_retryable

log = get_logger("pool")

# Dieu kien chon record: queued, HOAC running da het han TTL (node chet -> reclaim).
_PICK_WHERE = (
    "status='queued' "
    "OR (status='running' AND claim_expires_at IS NOT NULL AND claim_expires_at < :now)"
)
_RET = "id, service_id, username, password, totp_secret, email, attempt"

# SQLite: 1 UPDATE nguyen tu (write-lock tuan tu hoa -> khong 2 node trung record).
_CLAIM_SQLITE = text(
    f"UPDATE records SET status='running', node_id=:node_id, attempt=attempt+1, "
    f"claim_expires_at=:expires, updated_at=:now "
    f"WHERE id = (SELECT id FROM records WHERE {_PICK_WHERE} ORDER BY created_at LIMIT 1) "
    f"RETURNING {_RET}"
)

# Postgres: CTE + FOR UPDATE SKIP LOCKED -> N node claim SONG SONG, moi node khoa 1 row
# khac, bo qua row dang khoa -> khong trung, khong nghen (scale cao).
_CLAIM_PG = text(
    f"WITH picked AS (SELECT id FROM records WHERE {_PICK_WHERE} "
    f"ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED) "
    f"UPDATE records SET status='running', node_id=:node_id, attempt=attempt+1, "
    f"claim_expires_at=:expires, updated_at=:now "
    f"FROM picked WHERE records.id = picked.id "
    f"RETURNING records.id, records.service_id, records.username, records.password, "
    f"records.totp_secret, records.email, records.attempt"
)


class PoolService:
    def __init__(self, session: Session):
        self.session = session
        self.records = RecordRepository(session)
        self.orders = OrderRepository(session)

    # --- NODE goi ----------------------------------------------------------
    def claim_next(self, node_id: str, ttl_seconds: int = 300) -> dict | None:
        """Claim 1 record (atomic). None neu pool rong. Tra input cho node chay."""
        now = datetime.now(UTC)
        sql = _CLAIM_PG if self.session.bind.dialect.name == "postgresql" else _CLAIM_SQLITE
        row = self.session.execute(
            sql,
            {"node_id": node_id, "expires": now + timedelta(seconds=ttl_seconds), "now": now},
        ).first()
        if row is None:
            return None
        log.info("record_claimed", record_id=row.id, node_id=node_id, attempt=row.attempt)
        return {
            "record_id": row.id,
            "service_id": row.service_id,
            "username": row.username,
            "password": row.password,
            "totp_secret": row.totp_secret,
            "email": row.email,
            "attempt": row.attempt,
        }

    def report(self, record_id: str, result: dict, node_id: str = "") -> dict:
        """Node bao ket qua. success/failed(terminal)/retry. Doi status record + order."""
        record = self.records.get(record_id)
        if not record:
            return {"ok": False, "error": "record_not_found"}
        order = self.orders.get(record.order_id)

        record.result_json = json.dumps(result, ensure_ascii=False)
        record.duration = float(result.get("duration") or 0.0)
        record.claim_expires_at = None

        success = bool(result.get("success"))
        # Chap nhan CA 2 format: RunResult.to_dict (error={code,message}) va real_flow
        # flat (error=<code string>, cookies o top-level).
        err = result.get("error")
        if isinstance(err, dict):
            error_code = err.get("code")
            error_msg = err.get("message") or result.get("reason")
        else:
            error_code = result.get("error_code") or err
            error_msg = result.get("reason")

        if success:
            record.status = JobStatus.SUCCESS
            record.error_code = ""
            record.reason = ""
            session_data = (result.get("data") or {}).get("session") or {}
            cookies = (
                session_data.get("cookies")
                or (result.get("data") or {}).get("cookies")
                or result.get("cookies")
                or {}
            )
            record.cookies = json.dumps(cookies, ensure_ascii=False)
            outcome = "success"
        elif is_retryable(error_code) and record.attempt < RETRYABLE_MAX_ATTEMPTS:
            # loi ngoai login & con luot -> TRA LAI POOL (queued) de retry
            record.status = JobStatus.QUEUED
            record.error_code = error_code or ""
            record.reason = f"retry ({record.attempt}/{RETRYABLE_MAX_ATTEMPTS}): {error_msg or error_code}"
            record.node_id = ""
            log.info("record_requeue", record_id=record_id, attempt=record.attempt, code=error_code)
            return {"ok": False, "status": "requeued", "attempt": record.attempt}
        else:
            # loi login (terminal) HOAC het luot retry -> FAILED
            record.status = JobStatus.FAILED
            record.error_code = error_code or "failed"
            record.reason = error_msg or ""
            outcome = "failed"

        if order:
            self._sync_order(order)
        log.info("record_reported", record_id=record_id, outcome=outcome)
        return {"ok": success, "status": str(record.status)}

    # --- WEB / admin doc ---------------------------------------------------
    def list_records(
        self,
        order_id: str | None = None,
        status: str | None = None,
        user_id: str | None = None,
        limit: int = 500,
    ) -> list[Record]:
        """user_id = None -> tat ca (admin); nguoc lai chi record cua user do (join order)."""
        from sqlalchemy import select

        from app.db.models import Order

        stmt = select(Record).order_by(Record.created_at.desc()).limit(limit)
        if user_id is not None:
            stmt = stmt.join(Order, Record.order_id == Order.id).where(Order.user_id == user_id)
        if order_id:
            stmt = stmt.where(Record.order_id == order_id)
        if status:
            stmt = stmt.where(Record.status == status)
        return list(self.session.scalars(stmt))

    def stats(self, user_id: str | None = None) -> dict:
        from sqlalchemy import func, select

        from app.db.models import Order

        stmt = select(Record.status, func.count()).group_by(Record.status)
        if user_id is not None:
            stmt = stmt.join(Order, Record.order_id == Order.id).where(Order.user_id == user_id)
        return {str(s): n for s, n in self.session.execute(stmt).all()}

    def _sync_order(self, order: Order) -> None:
        # dem lai tu records de chinh xac (retry khong lam sai dem)
        from sqlalchemy import func, select

        # autoflush=False -> phai flush thay doi status cua record vua report TRUOC khi
        # dem, neu khong query aggregate se doc gia tri cu (dem lech 1 nhip).
        self.session.flush()
        prev_status = str(order.status)
        counts = dict(
            self.session.execute(
                select(Record.status, func.count())
                .where(Record.order_id == order.id)
                .group_by(Record.status)
            ).all()
        )
        order.completed_count = counts.get(JobStatus.SUCCESS, 0)
        order.failed_count = counts.get(JobStatus.FAILED, 0)
        done = order.completed_count + order.failed_count
        if done < order.quantity:
            order.status = OrderStatus.PROCESSING
        elif order.failed_count == 0:
            order.status = OrderStatus.COMPLETED
        elif order.completed_count == 0:
            order.status = OrderStatus.FAILED
        else:
            order.status = OrderStatus.PARTIAL

        # vao trang thai ket thuc lan dau -> bao cho chu don
        terminal = {OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.PARTIAL}
        if order.status in terminal and prev_status not in {str(s) for s in terminal}:
            self._notify_order_done(order)

    def _notify_order_done(self, order: Order) -> None:
        from app.core.enums import NotificationLevel, OrderStatus
        from app.modules.notifications import NotificationService

        level = {
            OrderStatus.COMPLETED: NotificationLevel.SUCCESS,
            OrderStatus.PARTIAL: NotificationLevel.WARNING,
            OrderStatus.FAILED: NotificationLevel.ERROR,
        }.get(order.status, NotificationLevel.INFO)
        NotificationService(self.session).notify(
            order.user_id,
            title=f"Don hang {order.status}",
            body=(
                f"Hoan tat: {order.completed_count} thanh cong / "
                f"{order.failed_count} that bai (tong {order.quantity})."
            ),
            level=level,
            ref_type="order",
            ref_id=order.id,
        )
