from __future__ import annotations

import time

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.core.errors import AccountLocked, InvalidCredentials, NeedMobileApp, RateLimited
from app.services.roblox import constants as C


class DetectLoginResultStep(Step):
    """Xac dinh ket qua cuoi: thanh cong -> lay cookie; that bai -> phan loai loi."""

    name = "detect_result"
    settle_timeout = 15   # cho toi khi co trang thai dut diem truoc khi phan loai

    def run(self, ctx: ExecutionContext) -> StepResult:
        self._wait_settle(ctx)   # tranh doc qua som -> "khong ro nguyen nhan"
        body = ctx.browser.text_of("body").lower()
        # Man app-promo mobile ("Continue in browser") = XUAT HIEN SAU khi giai xong
        # -> coi la THANH CONG (khac han man /not-approved doi quet QR).
        app_promo = "continue in browser" in body

        # Van ket o man "Account locked" (/not-approved) = CHUA thanh cong, du co
        # cookie. Tru khi da la man app-promo (da giai xong).
        if C.NOT_APPROVED_PATH in ctx.browser.current_url() and not app_promo:
            ctx.snapshot("account_locked")
            # Bien the doi xac thuc bang APP MOBILE (QUET QR) - khong co nut de bam
            # -> automation bo tay, danh dau fail rieng de update record.
            if any(k in body for k in ("scan this qr", "qr code")):
                raise NeedMobileApp("failed because need app", detail="not-approved: qr")
            raise AccountLocked("tai khoan bi khoa - chua mo duoc", detail=C.NOT_APPROVED_PATH)

        # thanh cong = app-promo (da giai xong) HOAC co cookie session that.
        cookies = ctx.browser.cookies()
        if app_promo or ctx.get("already_logged_in") or C.COOKIE_SESSION in cookies:
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

    def _wait_settle(self, ctx: ExecutionContext) -> None:
        """Cho toi khi trang co ket qua DUT DIEM roi moi phan loai:
        cookie / co chu loi / /not-approved / app-promo. Tranh doc luc con spinner
        -> "khong ro nguyen nhan"."""
        deadline = time.time() + self.settle_timeout
        while time.time() < deadline:
            if C.COOKIE_SESSION in ctx.browser.cookies():
                return
            if C.NOT_APPROVED_PATH in ctx.browser.current_url():
                return
            body = ctx.browser.text_of("body").lower()
            if "continue in browser" in body:
                return
            if ctx.browser.text_of(C.SEL_ERROR).strip():
                return
            time.sleep(1)

    def _capture_success(self, ctx: ExecutionContext, cookies: dict | None = None) -> StepResult:
        cookies = cookies or ctx.browser.cookies()
        ctx.session.cookies = cookies
        ctx.session.user_agent = ctx.browser.user_agent()
        ctx.session.tokens = {"session": cookies.get(C.COOKIE_SESSION, "")}
        # Da thu hoach cookie xong -> XOA cookie tren browser de phien sau mo len
        # khong dinh account nay (moi phien login account moi).
        ctx.browser.clear_cookies()
        return StepResult.ok(
            self.name,
            "dang nhap thanh cong",
            has_session_cookie=C.COOKIE_SESSION in cookies,
        )
