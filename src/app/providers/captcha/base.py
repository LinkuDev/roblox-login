"""Base cho cac dich vu captcha kieu "createTask -> poll getTaskResult".

2captcha, CapSolver, AntiCaptcha deu theo mo hinh nay nen chi khac payload mapping.
Provider kieu khac (vd tu host FunCaptcha solver) van co the implement thang
CaptchaSolver ma khong dung base nay.
"""

from __future__ import annotations

import time
from abc import abstractmethod
from typing import Any

import httpx

from app.core.config import CaptchaSettings, get_settings
from app.core.enums import CaptchaType
from app.core.errors import (
    CaptchaBalanceError,
    CaptchaError,
    CaptchaTimeout,
    CaptchaUnsolvable,
)
from app.core.logging import get_logger
from app.domain.models import CaptchaSolution, CaptchaTask
from app.domain.ports import CaptchaSolver
from app.core.registry import Registry

captcha_registry: Registry[CaptchaSolver] = Registry("captcha solver")


class HttpTaskSolver(CaptchaSolver):
    """Skeleton: tao task -> poll ket qua -> tra token."""

    base_url: str = ""
    create_path: str = "/createTask"
    result_path: str = "/getTaskResult"
    balance_path: str = "/getBalance"
    report_bad_path: str | None = None
    client_key_field: str = "clientKey"

    def __init__(self, api_key: str, config: CaptchaSettings | None = None):
        if not api_key:
            raise CaptchaError(f"thieu API key cho provider '{self.name}'")
        self.api_key = api_key
        self.config = config or get_settings().captcha
        self.log = get_logger("captcha", provider=self.name)
        self._client = httpx.Client(base_url=self.base_url, timeout=30.0)

    # --- phan provider phai cai dat ---------------------------------------
    @abstractmethod
    def build_task(self, task: CaptchaTask) -> dict[str, Any]:
        """Map CaptchaTask -> payload `task` rieng cua provider."""

    def extract_token(self, solution: dict[str, Any]) -> str:
        return solution.get("token") or solution.get("gRecaptchaResponse") or ""

    # --- luong chung -------------------------------------------------------
    def solve(self, task: CaptchaTask) -> CaptchaSolution:
        if not self.supports(task.type):
            raise CaptchaUnsolvable(
                f"{self.name} khong ho tro {task.type}", supported=sorted(self.supported)
            )

        started = time.perf_counter()
        task_id = self._create_task(task)
        self.log.info("captcha_created", task_id=task_id, type=str(task.type))

        deadline = time.monotonic() + self.config.timeout
        while time.monotonic() < deadline:
            time.sleep(self.config.poll_interval)
            payload = self._post(self.result_path, {"taskId": task_id})
            status = (payload.get("status") or "").lower()

            if status == "ready":
                sol = payload.get("solution") or {}
                token = self.extract_token(sol)
                if not token:
                    raise CaptchaUnsolvable("provider tra ve solution rong", raw=sol)
                elapsed = time.perf_counter() - started
                self.log.info("captcha_solved", task_id=task_id, seconds=round(elapsed, 1))
                return CaptchaSolution(
                    token=token,
                    provider=self.name,
                    task_id=str(task_id),
                    cost=self._to_float(payload.get("cost")),
                    solve_seconds=elapsed,
                    raw=payload,
                )
            if status not in {"processing", "idle", ""}:
                raise CaptchaUnsolvable(f"trang thai la {status}", raw=payload)

        raise CaptchaTimeout(
            f"qua {self.config.timeout}s van chua co ket qua", task_id=str(task_id)
        )

    def balance(self) -> float:
        payload = self._post(self.balance_path, {})
        return self._to_float(payload.get("balance")) or 0.0

    def report_bad(self, solution: CaptchaSolution) -> None:
        if not self.report_bad_path or not solution.task_id:
            return
        try:
            self._post(self.report_bad_path, {"taskId": solution.task_id})
        except CaptchaError as exc:
            self.log.debug("report_bad_failed", error=str(exc))

    def close(self) -> None:
        self._client.close()

    # --- ha tang -----------------------------------------------------------
    def _create_task(self, task: CaptchaTask) -> str:
        payload = self._post(self.create_path, {"task": self.build_task(task)})
        task_id = payload.get("taskId")
        if task_id is None:
            raise CaptchaError("provider khong tra taskId", raw=payload)
        return str(task_id)

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        data = {self.client_key_field: self.api_key, **body}
        try:
            resp = self._client.post(path, json=data)
            resp.raise_for_status()
            payload = resp.json()
        except httpx.HTTPError as exc:
            raise CaptchaError(f"loi goi {self.name}: {exc}") from exc
        except ValueError as exc:
            raise CaptchaError(f"{self.name} tra ve khong phai JSON") from exc

        self._raise_for_api_error(payload)
        return payload

    def _raise_for_api_error(self, payload: dict[str, Any]) -> None:
        if payload.get("errorId") in (0, None):
            return
        code = str(payload.get("errorCode") or "")
        desc = payload.get("errorDescription") or code or "loi khong ro"
        if "BALANCE" in code.upper() or "ZERO_BALANCE" in code.upper():
            raise CaptchaBalanceError(f"{self.name}: {desc}", code=code)
        if "UNSOLVABLE" in code.upper():
            raise CaptchaUnsolvable(f"{self.name}: {desc}", code=code)
        raise CaptchaError(f"{self.name}: {desc}", code=code)

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


PROXYLESS_SUPPORT = frozenset(
    {
        CaptchaType.FUNCAPTCHA,
        CaptchaType.RECAPTCHA_V2,
        CaptchaType.RECAPTCHA_V3,
        CaptchaType.HCAPTCHA,
        CaptchaType.TURNSTILE,
    }
)
