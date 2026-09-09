from __future__ import annotations

from pydantic import BaseModel, Field


class DepositCreateRequest(BaseModel):
    amount_points: int = Field(gt=0, examples=[10000])
    currency: str = Field(default="USDT", examples=["USDT", "USDC", "BTC"])


class DepositView(BaseModel):
    id: str
    status: str
    provider: str
    amount_points: int
    currency: str
    amount_crypto: float
    pay_address: str
    pay_url: str
    tx_hash: str
    expires_at: str | None
    confirmed_at: str | None
    created_at: str


class DepositConfirmRequest(BaseModel):
    """Admin confirm tay (provider manual / xu ly tranh chap)."""

    tx_hash: str = ""


class CryptoConfigResponse(BaseModel):
    """Cau hinh nap cho FE (gia, min, currency ho tro)."""

    enabled: bool
    provider: str
    usd_per_point: float      # 1 diem = bao nhieu USD (vd 0.03)
    min_usd: float            # nap toi thieu theo USD
    min_points: int           # min_usd quy ra diem (tien cho FE)
    currencies: list[str]
