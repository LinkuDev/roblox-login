"""Cay loi dung chung. Tang tren bat theo base class, khong bat Exception tran lan."""

from __future__ import annotations


class AppError(Exception):
    code = "app_error"
    http_status = 500

    def __init__(self, message: str = "", **context):
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__
        self.context = context

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "context": self.context}


# --- Business / SaaS ---------------------------------------------------------
class BusinessError(AppError):
    code = "business_error"
    http_status = 400


class NotFoundError(BusinessError):
    code = "not_found"
    http_status = 404


class AuthError(BusinessError):
    code = "unauthorized"
    http_status = 401


class PermissionDenied(BusinessError):
    code = "forbidden"
    http_status = 403


class InsufficientPoints(BusinessError):
    code = "insufficient_points"
    http_status = 402


# --- Provider / ha tang ------------------------------------------------------
class ProviderError(AppError):
    code = "provider_error"
    http_status = 502


class CaptchaError(ProviderError):
    code = "captcha_error"


class CaptchaTimeout(CaptchaError):
    code = "captcha_timeout"


class CaptchaUnsolvable(CaptchaError):
    code = "captcha_unsolvable"


class CaptchaBalanceError(CaptchaError):
    code = "captcha_no_balance"


class BrowserError(ProviderError):
    code = "browser_error"


class ProxyError(ProviderError):
    code = "proxy_error"


# --- Automation flow ---------------------------------------------------------
class AutomationError(AppError):
    code = "automation_error"


class StepFailed(AutomationError):
    code = "step_failed"

    def __init__(self, step: str, message: str = "", **ctx):
        super().__init__(message or f"step {step} failed", step=step, **ctx)
        self.step = step


class InvalidCredentials(AutomationError):
    code = "invalid_credentials"


class TwoFactorRequired(AutomationError):
    code = "two_factor_required"


class AccountLocked(AutomationError):
    code = "account_locked"


class NeedMobileApp(AutomationError):
    """Man /not-approved doi xac thuc bang app mobile (quet QR) - automation bo tay."""

    code = "need_mobile_app"


class RateLimited(AutomationError):
    code = "rate_limited"
