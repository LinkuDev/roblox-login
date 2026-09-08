"""Cong thanh toan crypto = 1 PORT. Doi nha cung cap (manual / NOWPayments / ...)
chi bang 1 dong config `CRYPTO_PROVIDER`, khong sua tang goi.

Provider chi lo GIAO TIEP voi gateway (tao invoice + xac thuc webhook). Nghiep vu
cong diem / idempotent nam o PaymentService.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.core.enums import DepositStatus
from app.core.registry import Registry


@dataclass
class Charge:
    """Ket qua tao invoice tu provider."""

    external_id: str                 # id ben provider (khop webhook ve sau)
    pay_address: str = ""            # dia chi vi user chuyen den
    pay_url: str = ""                # trang thanh toan (neu co)
    amount_crypto: float = 0.0       # so tien crypto phai tra
    currency: str = ""
    expires_at: datetime | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class WebhookEvent:
    """Su kien chuan hoa tu webhook provider."""

    external_id: str
    status: DepositStatus
    tx_hash: str = ""
    amount_crypto: float | None = None
    raw: dict = field(default_factory=dict)


class CryptoPaymentProvider(ABC):
    """Interface cho 1 cong crypto. Nhan CryptoSettings luc khoi tao."""

    def __init__(self, settings):
        self.settings = settings

    @abstractmethod
    def create_charge(
        self, deposit_id: str, amount_points: int, amount_usd: float, currency: str
    ) -> Charge:
        """Tao invoice/dia chi nhan tien cho 1 lenh nap."""

    @abstractmethod
    def parse_webhook(self, headers: dict[str, str], body: bytes) -> WebhookEvent:
        """Xac thuc + chuan hoa webhook. Raise ProviderError neu chu ky sai."""

    # Provider co the tu bao "khong dung webhook" (vd manual -> admin confirm tay).
    supports_webhook: bool = True


payment_registry: Registry[CryptoPaymentProvider] = Registry("crypto_payment_provider")


def build_payment_provider(settings) -> CryptoPaymentProvider:
    """Factory: doc CRYPTO_PROVIDER -> tra instance provider tuong ung."""
    # import de tu dang ky provider vao registry
    from app.modules.payments import providers  # noqa: F401

    cls = payment_registry.get(settings.provider)
    return cls(settings)
