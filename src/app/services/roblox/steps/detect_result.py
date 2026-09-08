from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.core.errors import AccountLocked, InvalidCredentials, NeedMobileApp, RateLimited
from app.services.roblox import constants as C


class DetectLoginResultStep(Step):
    """Xac dinh ket qua cuoi: thanh cong -> lay cookie; that bai -> phan loai loi."""

    name = "detect_result"

    def run(self, ctx: ExecutionContext) -> StepResult:
        # Van ket o man "Account locked" (/not-approved) = CHUA thanh cong, du co
        # cookie. Tranh bao success gia khi Arkose mo khoa chua qua.
        if C.NOT_APPROVED_PATH in ctx.browser.current_url():
            ctx.snapshot("account_locked")
            body = ctx.browser.text_of("body").lower()
            # Bien the doi xac thuc bang APP MOBILE (quet QR) - khong co nut de bam
            # -> automation bo tay, danh dau fail rieng de update record.
            if any(k in body for k in ("mobile app", "qr code", "scan this qr")):
                raise NeedMobileApp("failed because need app", detail="not-approved: mobile app")
            raise AccountLocked("tai khoan bi khoa - chua mo duoc", detail=C.NOT_APPROVED_PATH)

        # thanh cong = CO cookie session that (.ROBLOSECURITY). Khong dua vao navbar.
        cookies = ctx.browser.cookies()
        if ctx.get("already_logged_in") or C.COOKIE_SESSION in cookies:
            return self._capture_success(ctx, cookies)

        # that bai: doc thong bao loi de phan loai
        err = ctx.browser.text_of(C.SEL_ERROR).lower()
        ctx.snapshot("login_failed")

        if any(k in err for k in ("incorrect", "wrong", "sai", "invalid")):
            raise InvalidCredentials("sai tai khoan hoac mat khau", detail=err)
        if any(k in err for k in ("locked", "suspend", "khoa", "ban")):
            raise AccountLocked("tai khoan bi khoa", detail=err)
        if any(k in err for k in ("too many", "rate", "try again", "gioi han")):
            raise RateLimited("bi gioi han toc do", detail=err)

        return StepResult.failed(
            self.name, err or "dang nhap that bai khong ro nguyen nhan", "login_failed"
        )

    def _capture_success(self, ctx: ExecutionContext, cookies: dict | None = None) -> StepResult:
        cookies = cookies or ctx.browser.cookies()
        ctx.session.cookies = cookies
        ctx.session.user_agent = ctx.browser.user_agent()
        ctx.session.tokens = {"session": cookies.get(C.COOKIE_SESSION, "")}
        return StepResult.ok(
            self.name,
            "dang nhap thanh cong",
            has_session_cookie=C.COOKIE_SESSION in cookies,
        )
