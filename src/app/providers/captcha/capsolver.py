"""CapSolver - cung mo hinh createTask/getTaskResult, khac ten task type."""

from __future__ import annotations

from typing import Any

from app.core.enums import CaptchaType
from app.domain.models import CaptchaTask
from app.providers.captcha.base import PROXYLESS_SUPPORT, HttpTaskSolver, captcha_registry


@captcha_registry.register("capsolver")
class CapSolverSolver(HttpTaskSolver):
    name = "capsolver"
    base_url = "https://api.capsolver.com"
    supported = PROXYLESS_SUPPORT

    _TASK_TYPES = {
        CaptchaType.FUNCAPTCHA: "FunCaptchaTaskProxyLess",
        CaptchaType.RECAPTCHA_V2: "ReCaptchaV2TaskProxyLess",
        CaptchaType.RECAPTCHA_V3: "ReCaptchaV3TaskProxyLess",
        CaptchaType.HCAPTCHA: "HCaptchaTaskProxyLess",
        CaptchaType.TURNSTILE: "AntiTurnstileTaskProxyLess",
    }

    def build_task(self, task: CaptchaTask) -> dict[str, Any]:
        task_type = self._TASK_TYPES[task.type]
        if task.proxy:
            task_type = task_type.replace("ProxyLess", "")

        payload: dict[str, Any] = {"type": task_type, "websiteURL": task.website_url}

        if task.type is CaptchaType.FUNCAPTCHA:
            payload["websitePublicKey"] = task.website_key
            if task.api_subdomain:
                payload["funcaptchaApiJSSubdomain"] = task.api_subdomain
            if task.blob:
                payload["data"] = task.blob
        else:
            payload["websiteKey"] = task.website_key
            if task.action:
                payload["pageAction"] = task.action

        if task.proxy:
            payload["proxy"] = task.proxy.url
        payload.update(task.extra)
        return payload
