from __future__ import annotations

try:  # StrEnum co tu Python 3.11
    from enum import StrEnum
except ImportError:  # Python 3.10 -> fallback tuong duong
    from enum import Enum

    class StrEnum(str, Enum):
        """Tuong duong enum.StrEnum cho Python 3.10."""

        __str__ = str.__str__


class CaptchaType(StrEnum):
    FUNCAPTCHA = "funcaptcha"          # Arkose Labs - Roblox dung cai nay
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    IMAGE = "image"


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"        # da tao, cho tru diem / cho chay
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"        # 1 phan item thanh cong
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PointTxType(StrEnum):
    TOPUP = "topup"            # admin cong tay / sau nay la cong thanh toan
    SPEND = "spend"
    REFUND = "refund"
    BONUS = "bonus"
    ADJUST = "adjust"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class StepOutcome(StrEnum):
    OK = "ok"
    SKIPPED = "skipped"
    RETRY = "retry"
    FAILED = "failed"
