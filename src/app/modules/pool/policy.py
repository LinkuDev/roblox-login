"""Phan loai loi -> co retry hay khong.

- LOI LOGIN (terminal): account TU NO khong dang nhap duoc -> retry vo ich -> FAILED luon.
- LOI NGOAI LOGIN (ha tang): browser/proxy/captcha/mang/rate-limit/exception... -> tam
  thoi -> tra lai pool retry (toi da RETRYABLE_MAX_ATTEMPTS lan).
"""

from __future__ import annotations

# So lan CHAY toi da cho record gap loi ha tang (1 = chay lan dau, 2 = them 1 retry).
RETRYABLE_MAX_ATTEMPTS = 2

# error_code coi la LOI LOGIN (terminal, KHONG retry). Con lai deu la ha tang -> retry.
TERMINAL_LOGIN_CODES = frozenset(
    {
        "invalid_credentials",
        "account_locked",
        "need_mobile_app",
        "two_factor_required",
    }
)


def is_retryable(error_code: str | None) -> bool:
    """True neu loi NGOAI login (ha tang) -> nen tra lai pool retry."""
    code = (error_code or "").strip()
    if not code:
        return False   # khong co code (vd success) -> khong xet retry
    return code not in TERMINAL_LOGIN_CODES
