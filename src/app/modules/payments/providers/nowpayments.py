"""Provider `nowpayments` (cong crypto that).

Chi bat khi CRYPTO_API_KEY duoc set. Tao invoice qua REST, xac thuc IPN webhook
bang HMAC-SHA512 tren body JSON da sort key (dung chuan cua NOWPayments).
Dung urllib -> khong them dependency.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

from app.core.enums import DepositStatus
from app.core.errors import ProviderError
from app.modules.payments.provider import (
    Charge,
    CryptoPaymentProvider,
    WebhookEvent,
    payment_registry,
)

# payment_status cua NOWPayments -> trang thai noi bo.
_STATUS_MAP = {
    "waiting": DepositStatus.PENDING,
    "confirming": DepositStatus.CONFIRMING,
    "confirmed": DepositStatus.CONFIRMING,
    "sending": DepositStatus.CONFIRMING,
    "partially_paid": DepositStatus.CONFIRMING,
    "finished": DepositStatus.CONFIRMED,
    "failed": DepositStatus.FAILED,
    "refunded": DepositStatus.FAILED,
    "expired": DepositStatus.EXPIRED,
}


@payment_registry.register("nowpayments")
class NowPaymentsProvider(CryptoPaymentProvider):
    supports_webhook = True

    def _post(self, path: str, payload: dict) -> dict:
        if not self.settings.api_key:
            raise ProviderError("thieu CRYPTO_API_KEY cho nowpayments")
        url = f"{self.settings.api_base.rstrip('/')}{path}"
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"x-api-key": self.settings.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raise ProviderError(f"nowpayments {exc.code}: {exc.read().decode()[:200]}") from exc
        except OSError as exc:
            raise ProviderError(f"nowpayments khong ket noi duoc: {exc}") from exc

    def create_charge(
        self, deposit_id: str, amount_points: int, amount_usd: float, currency: str
    ) -> Charge:
        body = {
            "price_amount": round(amount_usd, 2),
            "price_currency": "usd",
            "pay_currency": currency.lower(),
            "order_id": deposit_id,
            "order_description": f"Topup {amount_points} points",
        }
        if self.settings.callback_base:
            body["ipn_callback_url"] = (
                f"{self.settings.callback_base.rstrip('/')}/api/v1/billing/deposits/webhook"
            )
        res = self._post("/payment", body)
        ttl = int(getattr(self.settings, "deposit_ttl_minutes", 60))
        return Charge(
            external_id=str(res.get("payment_id", "")),
            pay_address=res.get("pay_address", ""),
            pay_url=res.get("invoice_url", ""),
            amount_crypto=float(res.get("pay_amount") or 0),
            currency=(res.get("pay_currency") or currency).upper(),
            expires_at=datetime.now(UTC) + timedelta(minutes=ttl),
            raw=res,
        )

    def parse_webhook(self, headers: dict[str, str], body: bytes) -> WebhookEvent:
        secret = self.settings.ipn_secret
        if not secret:
            raise ProviderError("thieu CRYPTO_IPN_SECRET")
        sig = headers.get("x-nowpayments-sig") or headers.get("X-Nowpayments-Sig")
        payload = json.loads(body.decode())
        # HMAC-SHA512 tren JSON sort key (chuan NOWPayments).
        sorted_body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hmac.new(
            secret.encode(), sorted_body.encode(), hashlib.sha512
        ).hexdigest()
        if not sig or not hmac.compare_digest(sig, expected):
            raise ProviderError("chu ky IPN khong hop le")
        status = _STATUS_MAP.get(
            str(payload.get("payment_status", "")).lower(), DepositStatus.PENDING
        )
        return WebhookEvent(
            external_id=str(payload.get("payment_id", "")),
            status=status,
            tx_hash=str(payload.get("payin_hash") or payload.get("outcome_hash") or ""),
            amount_crypto=float(payload.get("actually_paid") or 0) or None,
            raw=payload,
        )
