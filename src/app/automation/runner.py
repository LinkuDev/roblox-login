"""Composition root cho 1 lan chay service.

Rap: settings -> providers (captcha/browser/proxy/storage) -> context -> service.
Day la noi duy nhat 'noi day' cac manh lai. API/worker/CLI deu goi ham nay.
"""

from __future__ import annotations

from app.automation.context import ExecutionContext
from app.automation.result import RunResult
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.domain.models import Credential
from app.domain.ports import CaptchaSolver, ProxyProvider
from app.providers.browser import build_browser
from app.providers.captcha import build_solver
from app.providers.proxy import build_proxy_provider
from app.providers.storage import LocalStorage
from app.services import build_service

log = get_logger("runner")


def run_service(
    service_id: str,
    credential: Credential,
    *,
    options: dict | None = None,
    job_id: str = "local",
    settings: Settings | None = None,
    solver: CaptchaSolver | None = None,
    proxy_provider: ProxyProvider | None = None,
    headless: bool | None = None,
) -> RunResult:
    settings = settings or get_settings()
    options = options or {}

    service = build_service(service_id)
    solver = solver or build_solver(settings=settings)
    proxy_provider = proxy_provider or build_proxy_provider(settings=settings)
    browser_provider = build_browser(settings=settings)
    storage = LocalStorage()

    proxy = proxy_provider.acquire(key=credential.username)
    log.info(
        "run_start",
        service=service_id,
        job_id=job_id,
        user=credential.username,
        proxy=bool(proxy),
        solver=solver.name,
    )

    try:
        with browser_provider.session(
            proxy=proxy,
            headless=headless,
            profile=options.get("profile"),
        ) as browser:
            ctx = ExecutionContext(
                credential=credential,
                browser=browser,
                solver=solver,
                settings=settings,
                proxy=proxy,
                storage=storage,
                job_id=job_id,
                options=options,
            )
            result = service.run(ctx)
    finally:
        if proxy:
            proxy_provider.release(proxy, healthy=True)
        solver.close()

    log.info("run_finish", service=service_id, job_id=job_id, success=result.success)
    return result
