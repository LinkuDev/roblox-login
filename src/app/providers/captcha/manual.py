"""Solver thu cong - dev/test: tu mo browser giai roi paste token.

Huu ich khi chua nap tien 2captcha ma van muon chay thu flow.
"""

from __future__ import annotations

import time

from app.core.enums import CaptchaType
from app.core.errors import CaptchaTimeout
from app.core.logging import get_logger
from app.domain.models import CaptchaSolution, CaptchaTask
from app.domain.ports import CaptchaSolver
from app.providers.captcha.base import PROXYLESS_SUPPORT, captcha_registry


@captcha_registry.register("manual")
class ManualSolver(CaptchaSolver):
    name = "manual"
    supported = PROXYLESS_SUPPORT

    def __init__(self, api_key: str = "", config=None):
        self.log = get_logger("captcha", provider=self.name)

    def solve(self, task: CaptchaTask) -> CaptchaSolution:
        started = time.perf_counter()
        print("\n=== GIAI CAPTCHA THU CONG ===")
        print(f"  loai : {task.type}")
        print(f"  url  : {task.website_url}")
        print(f"  key  : {task.website_key}")
        if task.blob:
            print(f"  blob : {task.blob[:80]}...")
        token = input("Dan token vao day (Enter de bo qua): ").strip()
        if not token:
            raise CaptchaTimeout("nguoi dung khong nhap token")
        return CaptchaSolution(
            token=token, provider=self.name, solve_seconds=time.perf_counter() - started
        )

    def balance(self) -> float:
        return float("inf")
