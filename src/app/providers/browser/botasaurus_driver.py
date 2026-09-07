"""Adapter Botasaurus -> BrowserSession port.

Chi file nay biet den Botasaurus. Muon doi sang Playwright/Camoufox thi viet
adapter khac va dang ky vao `browser_registry`, flow khong phai sua dong nao.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any

from app.core.config import BrowserSettings, get_settings
from app.core.errors import BrowserError
from app.core.logging import get_logger
from app.domain.models import Proxy
from app.domain.ports import BrowserProvider, BrowserSession
from app.providers.browser.base import browser_registry


class BotasaurusSession(BrowserSession):
    def __init__(self, driver: Any, settings: BrowserSettings):
        self._d = driver
        self._settings = settings
        self.log = get_logger("browser", provider="botasaurus")

    # --- dieu huong --------------------------------------------------------
    def goto(self, url: str, wait: float | None = None) -> None:
        try:
            self._d.get(url, wait=wait) if wait else self._d.get(url)
        except TypeError:
            self._d.get(url)
        except Exception as exc:
            raise BrowserError(f"khong mo duoc {url}: {exc}") from exc

    def current_url(self) -> str:
        return getattr(self._d, "current_url", "") or ""

    # --- element -----------------------------------------------------------
    def wait_for(self, selector: str, timeout: float | None = None) -> Any:
        timeout = timeout or self._settings.timeout
        try:
            el = self._d.wait_for_element(selector, wait=int(timeout))
        except Exception as exc:
            raise BrowserError(f"khong thay '{selector}' sau {timeout}s: {exc}") from exc
        if el is None:
            raise BrowserError(f"khong thay '{selector}' sau {timeout}s")
        return el

    def exists(self, selector: str, timeout: float = 0) -> bool:
        try:
            return self._d.select(selector, wait=int(timeout)) is not None
        except Exception:
            return False

    def type(self, selector: str, text: str, human: bool = True) -> None:
        el = self.wait_for(selector)
        try:
            el.type(text)
        except AttributeError:
            self._d.type(selector, text)

    def click(self, selector: str, timeout: float | None = None) -> None:
        el = self.wait_for(selector, timeout)
        try:
            el.click()
        except AttributeError:
            self._d.click(selector)

    def text_of(self, selector: str, default: str = "") -> str:
        try:
            el = self._d.select(selector, wait=2)
            if el is None:
                return default
            return (getattr(el, "text", None) or default).strip()
        except Exception:
            return default

    # --- js / state --------------------------------------------------------
    def run_js(self, script: str, *args: Any) -> Any:
        try:
            return self._d.run_js(script, *args) if args else self._d.run_js(script)
        except Exception as exc:
            raise BrowserError(f"run_js loi: {exc}") from exc

    def cookies(self) -> dict[str, str]:
        for attr in ("get_cookies_dict", "get_cookies_as_dict"):
            fn = getattr(self._d, attr, None)
            if callable(fn):
                return fn() or {}
        cookies = getattr(self._d, "get_cookies", lambda: [])() or []
        return {c["name"]: c["value"] for c in cookies if "name" in c}

    def user_agent(self) -> str:
        ua = getattr(self._d, "user_agent", None)
        if isinstance(ua, str) and ua:
            return ua
        try:
            return self.run_js("return navigator.userAgent") or ""
        except BrowserError:
            return ""

    def screenshot(self, path: str) -> str | None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        for attr in ("save_screenshot", "screenshot"):
            fn = getattr(self._d, attr, None)
            if callable(fn):
                try:
                    fn(path)
                    return path
                except Exception:
                    continue
        return None

    # --- iframe ------------------------------------------------------------
    def switch_to_iframe(self, selector: str) -> None:
        """Botasaurus xu ly iframe qua element handle.

        TODO(flow): xac nhan API iframe cua ban Botasaurus dang dung roi chot lai.
        """
        fn = getattr(self._d, "get_iframe_by_link", None) or getattr(self._d, "iframe", None)
        if not callable(fn):
            raise BrowserError(
                "driver khong ho tro switch iframe truc tiep - dung run_js voi "
                "contentWindow hoac chuyen sang solve captcha bang API token"
            )
        self._frame = fn(selector)

    def switch_to_main(self) -> None:
        self._frame = None

    def close(self) -> None:
        try:
            self._d.close()
        except Exception as exc:
            self.log.debug("close_failed", error=str(exc))

    @property
    def raw(self) -> Any:
        """Escape hatch: truy cap thang Driver khi thuc su can. Dung han che."""
        return self._d


@browser_registry.register("botasaurus")
class BotasaurusProvider(BrowserProvider):
    name = "botasaurus"

    def __init__(self, settings: BrowserSettings | None = None):
        self.settings = settings or get_settings().browser

    @contextmanager
    def session(
        self,
        *,
        proxy: Proxy | None = None,
        headless: bool | None = None,
        user_agent: str | None = None,
        profile: str | None = None,
        **kwargs: Any,
    ):
        try:
            from botasaurus.browser import Driver
        except ImportError as exc:  # pragma: no cover
            raise BrowserError(
                "chua cai botasaurus. Chay: pip install botasaurus botasaurus-driver"
            ) from exc

        opts: dict[str, Any] = {
            "headless": self.settings.headless if headless is None else headless,
            "window_size": self.settings.window_size,
        }
        if proxy:
            opts["proxy"] = proxy.url
        if ua := (user_agent or self.settings.user_agent):
            opts["user_agent"] = ua
        if profile:
            opts["profile"] = profile
        opts.update(kwargs)

        driver = Driver(**opts)
        session = BotasaurusSession(driver, self.settings)
        try:
            yield session
        finally:
            session.close()
