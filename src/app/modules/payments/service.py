"""Nghiep vu nap diem qua crypto.

Luong: user tao lenh nap -> provider tra dia chi/invoice -> user chuyen tien ->
webhook provider (hoac admin confirm) -> CONG DIEM DUNG 1 LAN (idempotent theo
trang thai CONFIRMED). Provider chi lo giao tiep gateway (xem provider.py).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.enums import DepositStatus, NotificationLevel, PointTxType
from app.core.errors import BusinessError, NotFoundError
from app.db.models import Deposit
from app.db.repositories import DepositRepository
from app.modules.billing import BillingService
from app.modules.notifications import NotificationService
from app.modules.payments.provider import WebhookEvent, build_payment_provider

# trang thai terminal -> khong doi nua.
_TERMINAL = {DepositStatus.CONFIRMED, DepositStatus.EXPIRED, DepositStatus.CANCELLED}


class PaymentService:
    def __init__(self, session: Session, settings=None):
        self.session = session
        self.repo = DepositRepository(session)
        self.billing = BillingService(session)
        self.notify = NotificationService(session)
        if settings is None:
            from app.core.config import get_settings

            settings = get_settings().crypto
        self.settings = settings

    # --- user --------------------------------------------------------------
    def create_deposit(self, user_id: str, amount_points: int, currency: str) -> dict:
        if not self.settings.enabled:
            raise BusinessError("nap crypto dang tat")
        if amount_points < self.settings.min_points:
            raise BusinessError(f"nap toi thieu {self.settings.min_points} diem")
        currency = (currency or "").upper() or self.settings.currency_list()[0]
        if currency not in self.settings.currency_list():
            raise BusinessError(f"currency khong ho tro: {currency}")

        rate = self.settings.points_per_usd
        amount_usd = round(amount_points / rate, 8) if rate else 0.0

        deposit = self.repo.add(
            Deposit(
                user_id=user_id,
                provider=self.settings.provider,
                status=DepositStatus.PENDING,
                amount_points=amount_points,
                currency=currency,
                rate_points_per_usd=rate,
            )
        )
        self.session.flush()   # co deposit.id lam order_id/external_id

        provider = build_payment_provider(self.settings)
        charge = provider.create_charge(deposit.id, amount_points, amount_usd, currency)

        deposit.external_id = charge.external_id or deposit.id
        deposit.pay_address = charge.pay_address
        deposit.pay_url = charge.pay_url
        deposit.amount_crypto = charge.amount_crypto or amount_usd
        deposit.currency = charge.currency or currency
        deposit.expires_at = charge.expires_at
        deposit.raw_json = json.dumps(charge.raw, ensure_ascii=False)
        return self._view(deposit)

    def get(self, deposit_id: str, user_id: str | None = None) -> dict:
        deposit = self.repo.get(deposit_id)
        if not deposit or (user_id and deposit.user_id != user_id):
            raise NotFoundError("khong tim thay lenh nap")
        self._maybe_expire(deposit)
        return self._view(deposit)

    def list_for_user(self, user_id: str) -> list[dict]:
        out = []
        for d in self.repo.by_user(user_id):
            self._maybe_expire(d)
            out.append(self._view(d))
        return out

    # --- webhook / admin ---------------------------------------------------
    def handle_webhook(self, headers: dict[str, str], body: bytes) -> dict:
        provider = build_payment_provider(self.settings)
        event: WebhookEvent = provider.parse_webhook(headers, body)
        deposit = self.repo.by_external_id(event.external_id) or self.repo.get(
            event.external_id
        )
        if not deposit:
            raise NotFoundError("khong khop lenh nap")
        return self._apply_status(deposit, event.status, event.tx_hash, event.raw)

    def admin_confirm(self, deposit_id: str, tx_hash: str = "") -> dict:
        deposit = self.repo.get(deposit_id)
        if not deposit:
            raise NotFoundError("khong tim thay lenh nap")
        return self._apply_status(deposit, DepositStatus.CONFIRMED, tx_hash, {"by": "admin"})

    def cancel(self, deposit_id: str, user_id: str) -> dict:
        deposit = self.repo.get(deposit_id)
        if not deposit or deposit.user_id != user_id:
            raise NotFoundError("khong tim thay lenh nap")
        if deposit.status in _TERMINAL:
            raise BusinessError("lenh nap da ket thuc, khong the huy")
        deposit.status = DepositStatus.CANCELLED
        return self._view(deposit)

    # --- noi bo ------------------------------------------------------------
    def _apply_status(
        self, deposit: Deposit, new_status: DepositStatus, tx_hash: str, raw: dict
    ) -> dict:
        if tx_hash:
            deposit.tx_hash = tx_hash
        if raw:
            deposit.raw_json = json.dumps(raw, ensure_ascii=False)

        # da confirm roi -> KHONG cong lai (idempotent, chong webhook lap).
        if deposit.status == DepositStatus.CONFIRMED:
            return self._view(deposit)

        if new_status == DepositStatus.CONFIRMED:
            self._credit(deposit)
        elif new_status in (DepositStatus.CONFIRMING, DepositStatus.FAILED, DepositStatus.EXPIRED):
            deposit.status = new_status
        return self._view(deposit)

    def _credit(self, deposit: Deposit) -> None:
        deposit.status = DepositStatus.CONFIRMED
        deposit.confirmed_at = datetime.now(UTC)
        self.billing.topup(
            deposit.user_id,
            deposit.amount_points,
            note=f"nap crypto {deposit.currency}",
            tx_type=PointTxType.DEPOSIT,
            ref_type="deposit",
            ref_id=deposit.id,
        )
        self.notify.notify(
            deposit.user_id,
            title="Nap diem thanh cong",
            body=f"Da cong {deposit.amount_points} diem vao vi ({deposit.currency}).",
            level=NotificationLevel.SUCCESS,
            ref_type="deposit",
            ref_id=deposit.id,
        )

    def _maybe_expire(self, deposit: Deposit) -> None:
        if (
            deposit.status in (DepositStatus.PENDING, DepositStatus.CONFIRMING)
            and deposit.expires_at
            and deposit.expires_at < datetime.now(UTC)
        ):
            deposit.status = DepositStatus.EXPIRED

    @staticmethod
    def _view(d: Deposit) -> dict:
        return {
            "id": d.id,
            "status": d.status,
            "provider": d.provider,
            "amount_points": d.amount_points,
            "currency": d.currency,
            "amount_crypto": float(d.amount_crypto or 0),
            "pay_address": d.pay_address,
            "pay_url": d.pay_url,
            "tx_hash": d.tx_hash,
            "expires_at": d.expires_at.isoformat() if d.expires_at else None,
            "confirmed_at": d.confirmed_at.isoformat() if d.confirmed_at else None,
            "created_at": d.created_at.isoformat(),
        }
