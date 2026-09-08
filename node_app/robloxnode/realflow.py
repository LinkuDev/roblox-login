"""run_flow THAT: claim record -> mo Chrome -> chay flow roblox.login.

Import flow-core (app.automation.runner) LAZY trong ham -> node van import/config
duoc ngay ca khi chua co flow-core. Solver captcha build tu NodeConfig (provider +
clientKey). Chua co key -> null solver (buoc captcha optional se fail nhe).
"""

from __future__ import annotations

from robloxnode.config import NodeConfig
from robloxnode.pool import Record


def _build_solver(cfg: NodeConfig):
    """Solver tu config node. None neu chua co key / provider khong ton tai."""
    if not cfg.captcha_key:
        return None
    try:
        from app.providers.captcha.base import captcha_registry

        return captcha_registry.get(cfg.captcha_provider)(api_key=cfg.captcha_key)
    except Exception:
        return None


def real_flow(record: Record) -> dict:
    try:
        from app.automation.runner import run_service
        from app.core.config import Settings
        from app.core.errors import CaptchaError
        from app.domain.models import Credential
        from app.domain.ports.captcha import CaptchaSolver
    except ImportError as exc:  # chua co flow-core
        return {"success": False, "error": "flow_core_missing", "reason": str(exc)}

    cfg = NodeConfig.load()
    solver = _build_solver(cfg)

    # Key tu UI node -> bom vao extension YesCaptcha (extension tu giai in-page).
    # Mot nguon su that: doi key trong app = doi ca solver lan extension.
    settings = Settings()
    if cfg.captcha_key:
        settings.browser.captcha_client_key = cfg.captcha_key
    if solver is None:
        class _NullSolver(CaptchaSolver):
            name = "none"

            def solve(self, task):
                raise CaptchaError("captcha provider chua cau hinh tren node")

            def balance(self) -> float:
                return 0.0

            def close(self) -> None:
                pass

        solver = _NullSolver()

    cred = Credential(username=record.username, password=record.password)
    result = run_service(
        "roblox.login", cred, job_id=record.id, headless=False, solver=solver,
        settings=settings,
    )

    session = (result.data or {}).get("session") or {}
    return {
        "success": result.success,
        "error": result.error_code,
        "reason": result.error_message,
        "cookies": session.get("cookies") or {},
    }
