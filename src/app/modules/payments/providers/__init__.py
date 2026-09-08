# import cac provider de chung tu dang ky vao payment_registry.
from app.modules.payments.providers import manual, nowpayments  # noqa: F401

__all__ = ["manual", "nowpayments"]
