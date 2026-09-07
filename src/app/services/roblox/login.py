"""Service: roblox.login - dang nhap co ban + giai captcha + 2FA."""

from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.flow import Flow
from app.services.base import Service, ServiceSpec
from app.services.registry import service_registry
from app.services.roblox.steps import (
    DetectLoginResultStep,
    FillCredentialsStep,
    Handle2FAStep,
    OpenLoginPageStep,
    SolveCaptchaStep,
    SubmitLoginStep,
)


@service_registry.register("roblox.login")
class RobloxLoginService(Service):
    spec = ServiceSpec(
        id="roblox.login",
        name="Roblox Login",
        category="roblox",
        price_points=1,
        description="Dang nhap tai khoan Roblox, giai captcha, lay session cookie.",
        input_fields=("username", "password", "totp_secret"),
        tags=("login", "captcha", "session"),
    )

    def build_flow(self, ctx: ExecutionContext) -> Flow:
        # Thu tu step = thu tu chay. Them/bot step o day ma khong dung logic khac.
        return Flow(
            self.spec.id,
            [
                OpenLoginPageStep(),
                FillCredentialsStep(),
                SubmitLoginStep(),
                SolveCaptchaStep(),   # tu bo qua neu khong co captcha
                Handle2FAStep(),      # tu bo qua neu khong bat 2FA
                DetectLoginResultStep(),
            ],
        )
