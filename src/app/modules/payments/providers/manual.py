"""Provider `manual` (mac dinh / dev).

Khong goi gateway ngoai: hien dia chi vi cau hinh san (CRYPTO_WALLET_ADDRESS) cho
user chuyen tien, roi ADMIN confirm tay (POST /admin/deposits/{id}/confirm) hoac 1
webhook noi bo goi toi. Dung de chay thu toan bo luong ma khong can khoa API that.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.modules.payments.provider import (
    Charge,
    CryptoPaymentProvider,
    payment_registry,
)


@payment_registry.register("manual")
class ManualProvider(CryptoPaymentProvider):
    supports_webhook = False

    def create_charge(
        self, deposit_id: str, amount_points: int, amount_usd: float, currency: str
    ) -> Charge:
        ttl = int(getattr(self.settings, "deposit_ttl_minutes", 60))
        return Charge(
            external_id=deposit_id,   # tu dung id noi bo lam external_id
            pay_address=self.settings.wallet_address,
            pay_url="",
            amount_crypto=round(amount_usd, 8),   # coi 1 stablecoin ~ 1 USD
            currency=currency,
            expires_at=datetime.now(UTC) + timedelta(minutes=ttl),
            raw={"mode": "manual"},
        )

    def parse_webhook(self, headers, body):
        from app.core.errors import BusinessError

        raise BusinessError("provider 'manual' khong dung webhook - dung admin confirm")
