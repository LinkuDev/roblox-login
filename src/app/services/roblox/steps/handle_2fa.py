from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.core.errors import TwoFactorRequired
from app.services.roblox import constants as C


class Handle2FAStep(Step):
    name = "handle_2fa"
    optional = True

    def should_run(self, ctx: ExecutionContext) -> bool:
        if ctx.get("already_logged_in"):
            return False
        return ctx.browser.exists(C.SEL_2FA_INPUT, timeout=5)

    def run(self, ctx: ExecutionContext) -> StepResult:
        cred = ctx.credential
        if not cred.totp_secret:
            # tk co bat 2FA nhung khong cung cap secret -> bao ro
            raise TwoFactorRequired("tai khoan yeu cau 2FA nhung khong co totp_secret")

        code = self._totp(cred.totp_secret)
        ctx.browser.type(C.SEL_2FA_INPUT, code)
        if ctx.browser.exists(C.SEL_2FA_SUBMIT, timeout=2):
            ctx.browser.click(C.SEL_2FA_SUBMIT)
        return StepResult.ok(self.name, "da nhap ma 2FA")

    @staticmethod
    def _totp(secret: str) -> str:
        """Sinh ma TOTP. Uu tien pyotp neu co, khong thi tu tinh (RFC 6238)."""
        try:
            import pyotp

            return pyotp.TOTP(secret).now()
        except ImportError:
            return _totp_fallback(secret)


def _totp_fallback(secret: str) -> str:
    import base64
    import hashlib
    import hmac
    import struct
    import time

    key = base64.b32decode(secret.upper() + "=" * ((8 - len(secret) % 8) % 8))
    counter = struct.pack(">Q", int(time.time()) // 30)
    digest = hmac.new(key, counter, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code:06d}"
