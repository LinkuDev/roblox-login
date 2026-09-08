"""Man "Account locked" hau dang nhap (/not-approved).

Sau khi login co cookie, Roblox co the chuyen sang /not-approved ("We've detected
suspicious activity... confirm you're a human"). Nut Continue nam trong DOM -> bam
bang automation -> Arkose hien -> extension YesCaptcha tu giai. Neu that bai hien
"Try unlocking again" -> bam Continue lai (toi da max_attempts lan).

Khi vao man nay moi CHUYEN sang MOBILE: thu nho + REPOSITION cua so vao o luoi
(khong de len cac phien khac), emulate viewport dien thoai, reload.

Re-entry: dang doi giai, neu captcha bien mat va modal quay lai (Continue lai hien
/ dang loading) ma van o /not-approved -> reload, coi nhu vua vao lai luong
not-approved va lam lai (moi lan re-entry tang timeout de khong dinh timeout cu).
"""

from __future__ import annotations

import json
import time

from app.automation.context import ExecutionContext
from app.automation.result import StepResult
from app.automation.step import Step
from app.services.roblox import constants as C

# Nut unlock co text CHINH XAC "Continue" (KHONG phai "Continue in App"/
# "Continue in browser" cua man app-promo -> tranh bam nham mo app store).
_HAS_CONTINUE = (
    "return [...document.querySelectorAll('button,[role=button]')]"
    ".some(x=>(x.innerText||'').trim().toLowerCase()==='continue');"
)
_CLICK_CONTINUE = (
    "const b=[...document.querySelectorAll('button,[role=button]')]"
    ".find(x=>(x.innerText||'').trim().toLowerCase()==='continue');"
    "if(b){b.scrollIntoView({block:'center'});b.click();return true;}return false;"
)

# Chup TOAN BO trang thai man /not-approved trong 1 lan run_js (nhanh, nhat quan).
# LUU Y: KHONG bat spinner ngam cua trang (footer/lazy-load) -> tranh false "loading"
# khi nut Continue van bam duoc. Chi coi "busy" khi CHINH nut trong modal disabled/
# aria-busy (spinner ben trong nut sau khi bam).
_STATE_JS = (
    "const url=location.href.toLowerCase();"
    "const body=(document.body.innerText||'').toLowerCase();"
    "const vis=el=>!!(el&&(el.offsetParent!==null||el.getClientRects().length));"
    "const btns=[...document.querySelectorAll('button,[role=button]')];"
    "const cont=btns.find(x=>(x.innerText||'').trim().toLowerCase()==='continue');"
    "const continueClickable=!!(cont&&!cont.disabled&&"
    "cont.getAttribute('aria-busy')!=='true'&&vis(cont));"
    "const busy=btns.some(x=>vis(x)&&(x.disabled||x.getAttribute('aria-busy')==='true'));"
    f"const captcha=!!document.querySelector({json.dumps(C.SEL_CAPTCHA_FRAME)});"
    "return {"
    "notApproved: url.includes('/not-approved'),"
    f"appPromo: {json.dumps(list(C.APP_PROMO_TEXTS))}.some(t=>body.includes(t)),"
    "qr: body.includes('scan this qr')||body.includes('qr code'),"
    "retry: body.includes('try unlocking again')||body.includes(\"weren't able to unlock\"),"
    "captcha: captcha,"
    "continueClickable: continueClickable,"
    "busy: busy,"
    "modal: !!document.querySelector("
    "\"[role=dialog],[data-internal-page-name='NotApproved']\")"
    "};"
)

# Sentinel: vong doi bao "can re-entry" (reload roi vao lai tu dau)
_RESTART = object()


class HandleAccountLockedStep(Step):
    name = "handle_account_locked"
    optional = True          # khong phai acc nao cung bi khoa
    max_attempts = 3         # so lan bam Continue toi da moi lan vao
    max_reentries = 3        # so lan vao lai luong (khi modal reset)
    reentry_timeout_bonus = 30   # moi lan re-entry cong them (giay) vao timeout cho

    redirect_wait = 8   # giay cho redirect /not-approved sau login (co the cham)

    def should_run(self, ctx: ExecutionContext) -> bool:
        # Redirect sang /not-approved co the den VAI GIAY sau login -> poll, dung
        # check 1 lan roi skip (skip nham -> detect_result se bao success tren cookie).
        deadline = time.time() + self.redirect_wait
        while time.time() < deadline:
            url = ctx.browser.current_url()
            if C.NOT_APPROVED_PATH in url:
                return True
            if "/home" in url:   # da vao home that -> khong khoa, khoi cho
                return False
            time.sleep(1)
        return C.NOT_APPROVED_PATH in ctx.browser.current_url()

    def run(self, ctx: ExecutionContext) -> StepResult:
        for reentry in range(self.max_reentries + 1):
            # timeout cho moi lan re-entry tang len (khoi dinh timeout cu)
            extra_timeout = reentry * self.reentry_timeout_bonus
            self._enter_mobile(ctx)

            # Man doi APP MOBILE (quet QR, khong Continue) -> bo tay, detect_result danh dau.
            if not ctx.browser.run_js(_HAS_CONTINUE):
                return StepResult.skipped(self.name, "khong co Continue - detect_result xu ly")

            result = self._try_unlock(ctx, extra_timeout=extra_timeout)
            if result is not _RESTART:
                return result   # ok / skipped / failed
            ctx.log.info("account_locked_reentry", reentry=reentry + 1)

        # het luot re-entry ma van khoa
        if C.NOT_APPROVED_PATH not in ctx.browser.current_url():
            return StepResult.ok(self.name, "da mo khoa")
        ctx.snapshot("account_locked")
        return StepResult.failed(
            self.name, "khong mo khoa duoc (Arkose chua giai)", "account_locked"
        )

    # --- chuyen sang mobile + dat vao o luoi -------------------------------
    def _enter_mobile(self, ctx: ExecutionContext) -> None:
        """Thu nho + REPOSITION cua so vao o luoi (task 1: chi tile o che do mobile),
        emulate viewport dien thoai, reload de trang render lai mobile."""
        pos = ctx.option("window_position")   # (x, y) o luoi tu agent, co the None
        if pos:
            ctx.browser.resize_window(*C.MOBILE_WINDOW, x=int(pos[0]), y=int(pos[1]))
        else:
            ctx.browser.resize_window(*C.MOBILE_WINDOW)
        mw, mh = C.MOBILE_VIEWPORT
        ctx.browser.emulate(
            mw, mh, mobile=True,
            user_agent=C.MOBILE_USER_AGENT,
            client_hints=C.MOBILE_CLIENT_HINTS,
            scale_factor=3.0,
        )
        ctx.browser.reload()
        time.sleep(3)  # cho reload xong

    # --- state machine: poll lien tuc trang thai roi phan ung ---------------
    poll = 2.0               # chu ky capture trang thai (giay)
    max_continue = 4         # so lan bam Continue toi da trong 1 lan vao
    loading_grace = 5        # so poll "loading" lien tiep truoc khi F5
    max_refresh = 3          # so lan F5 do loading truoc khi RE-ENTRY

    def _try_unlock(self, ctx: ExecutionContext, extra_timeout: int = 0):
        """Poll trang thai lien tuc va phan ung:
          - da mo khoa (roi /not-approved / app-promo) -> ok
          - doi app (QR)                               -> skipped
          - dang giai (captcha hien)                   -> DOI
          - co modal Continue (khong spinner)          -> BAM Continue
          - loading keo dai (spinner / modal trong)    -> F5; F5 nhieu lan -> RE-ENTRY
          - "try unlocking again"                      -> BAM Continue
        Tra StepResult (ok/skipped) hoac `_RESTART` (het gio / can vao lai)."""
        s = ctx.settings.captcha
        deadline = time.time() + s.timeout + extra_timeout
        continue_clicks = 0
        loading_streak = 0
        refreshes = 0

        while time.time() < deadline:
            st = self._detect_state(ctx)

            if st == "unlocked":
                # DEBOUNCE: sau khi bam Continue co the transient roi /not-approved
                # trong khi challenge chua kip len -> xac nhan on dinh moi bao mo khoa.
                time.sleep(4)
                if self._detect_state(ctx) == "unlocked":
                    return StepResult.ok(self.name, "da mo khoa", continues=continue_clicks)
                continue   # transient -> tiep tuc xu ly (challenge vua hien)
            if st == "need_app":
                ctx.log.info("account_locked_need_app")
                return StepResult.skipped(self.name, "doi app mobile - detect_result xu ly")

            if st == "solving":
                loading_streak = 0
                time.sleep(self.poll)
                continue

            if st in ("continue_modal", "retry_prompt"):
                loading_streak = 0
                if continue_clicks >= self.max_continue:
                    ctx.log.info("account_locked_continue_capped")
                    return _RESTART   # bam nhieu roi van khoa -> vao lai
                clicked = bool(ctx.browser.run_js(_CLICK_CONTINUE))
                continue_clicks += 1
                ctx.log.info("account_locked_continue", state=st, n=continue_clicks, clicked=clicked)
                time.sleep(self.poll)
                continue

            if st == "loading":
                loading_streak += 1
                if loading_streak >= self.loading_grace:
                    # modal Continue dang loading ket -> F5 (tai lai trang)
                    refreshes += 1
                    loading_streak = 0
                    ctx.log.info("account_locked_loading_f5", refresh=refreshes)
                    if refreshes > self.max_refresh:
                        return _RESTART   # F5 hoai van loading -> vao lai tu dau
                    ctx.browser.reload()
                    time.sleep(3)
                    # F5 = coi nhu vao lai tu dau -> RESET deadline ve full timeout
                    deadline = time.time() + s.timeout + extra_timeout
                else:
                    time.sleep(self.poll)
                continue

            # unknown -> doi ngan roi capture lai
            time.sleep(self.poll)

        # het gio: con luot re-entry thi run() vao lai, het thi failed
        if C.NOT_APPROVED_PATH not in ctx.browser.current_url():
            return StepResult.ok(self.name, "da mo khoa")
        return _RESTART

    # --- detector: chup trang thai hien tai (1 lan run_js) ------------------
    def _detect_state(self, ctx: ExecutionContext) -> str:
        """Phan loai trang thai man /not-approved. Tra 1 trong:
        unlocked | need_app | solving | continue_modal | retry_prompt | loading | unknown."""
        try:
            raw = ctx.browser.run_js(_STATE_JS)
            st = raw if isinstance(raw, dict) else json.loads(raw)
        except Exception:  # noqa: BLE001 - loi doc DOM -> coi la loading transient
            return "loading"

        # THU TU QUAN TRONG: challenge/modal dang hoat dong PHAI duoc uu tien hon tin
        # hieu URL-roi-not-approved. Sau khi bam Continue, URL co the transient roi
        # /not-approved trong khi challenge (Arkose/modal) van dang len -> neu check
        # "unlocked" truoc se thoat SOM -> false success (bug da gap).
        if st.get("captcha"):
            return "solving"          # challenge Arkose dang hien -> giai (ke ca URL da doi)
        if st.get("retry"):
            return "retry_prompt"
        if st.get("continueClickable"):
            return "continue_modal"
        if st.get("busy"):
            return "loading"          # nut dang spinner sau khi bam
        if st.get("qr"):
            return "need_app"
        # Chi coi UNLOCKED khi KHONG con challenge/continue/busy/modal ma da roi
        # not-approved (hoac hien app-promo). Con modal -> loading (cho tiep).
        if (not st.get("notApproved") or st.get("appPromo")) and not st.get("modal"):
            return "unlocked"
        if st.get("modal"):
            return "loading"
        return "unknown"

    def _body(self, ctx: ExecutionContext) -> str:
        return ctx.browser.text_of("body").lower()
