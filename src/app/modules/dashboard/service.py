"""Tong hop so lieu cho trang dashboard. Doc-only, gom nhieu bang thanh 1 payload
de FE goi 1 lan. user_id=None -> so lieu toan he thong (admin)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import JobStatus, PointTxType, UserRole
from app.db.models import (
    Deposit,
    Order,
    PointTransaction,
    Record,
    User,
    Wallet,
)
from app.modules.billing import BillingService
from app.modules.notifications import NotificationService


class DashboardService:
    def __init__(self, session: Session):
        self.session = session

    def for_user(self, user_id: str) -> dict:
        balance = BillingService(self.session).balance(user_id)
        orders = self._order_counts(user_id)
        records = self._record_counts(user_id)
        spend = self._spend_total(user_id)
        return {
            "scope": "user",
            "balance": balance,
            "orders": orders,
            "records": records,
            "spent_points": spend,
            "success_rate": self._success_rate(records),
            "unread_notifications": NotificationService(self.session).unread_count(user_id),
            "recent_orders": self._recent_orders(user_id),
            "recent_transactions": self._recent_txns(user_id),
        }

    def admin_overview(self) -> dict:
        total_users = self.session.scalar(select(func.count()).select_from(User)) or 0
        total_balance = self.session.scalar(select(func.coalesce(func.sum(Wallet.balance), 0)))
        confirmed_deposits = self.session.scalar(
            select(func.count()).select_from(Deposit).where(Deposit.status == "confirmed")
        ) or 0
        return {
            "scope": "admin",
            "users": total_users,
            "points_in_circulation": int(total_balance or 0),
            "orders": self._order_counts(None),
            "records": self._record_counts(None),
            "confirmed_deposits": confirmed_deposits,
            "recent_orders": self._recent_orders(None),
        }

    # --- helpers -----------------------------------------------------------
    def _order_counts(self, user_id: str | None) -> dict:
        stmt = select(Order.status, func.count()).group_by(Order.status)
        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)
        counts = {str(s): n for s, n in self.session.execute(stmt).all()}
        counts["total"] = sum(counts.values())
        return counts

    def _record_counts(self, user_id: str | None) -> dict:
        stmt = select(Record.status, func.count()).group_by(Record.status)
        if user_id is not None:
            stmt = stmt.join(Order, Record.order_id == Order.id).where(
                Order.user_id == user_id
            )
        base = {str(s): 0 for s in (JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.SUCCESS, JobStatus.FAILED)}
        base.update({str(s): n for s, n in self.session.execute(stmt).all()})
        base["total"] = sum(v for k, v in base.items() if k != "total")
        return base

    def _spend_total(self, user_id: str) -> int:
        stmt = (
            select(func.coalesce(func.sum(func.abs(PointTransaction.amount)), 0))
            .join(Wallet, PointTransaction.wallet_id == Wallet.id)
            .where(Wallet.user_id == user_id, PointTransaction.type == PointTxType.SPEND)
        )
        return int(self.session.scalar(stmt) or 0)

    def _success_rate(self, records: dict) -> float:
        done = records.get(str(JobStatus.SUCCESS), 0) + records.get(str(JobStatus.FAILED), 0)
        if not done:
            return 0.0
        return round(records.get(str(JobStatus.SUCCESS), 0) / done * 100, 1)

    def _recent_orders(self, user_id: str | None, limit: int = 5) -> list[dict]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit)
        if user_id is not None:
            stmt = stmt.where(Order.user_id == user_id)
        return [
            {
                "id": o.id,
                "service_id": o.service_id,
                "status": o.status,
                "quantity": o.quantity,
                "completed_count": o.completed_count,
                "failed_count": o.failed_count,
                "total_price": o.total_price,
                "created_at": o.created_at.isoformat(),
            }
            for o in self.session.scalars(stmt)
        ]

    def _recent_txns(self, user_id: str, limit: int = 5) -> list[dict]:
        stmt = (
            select(PointTransaction)
            .join(Wallet, PointTransaction.wallet_id == Wallet.id)
            .where(Wallet.user_id == user_id)
            .order_by(PointTransaction.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "type": t.type,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "note": t.note,
                "created_at": t.created_at.isoformat(),
            }
            for t in self.session.scalars(stmt)
        ]
