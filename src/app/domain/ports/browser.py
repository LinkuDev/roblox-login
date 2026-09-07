"""Port browser.

Automation steps chi noi chuyen voi interface nay -> co the thay Botasaurus bang
Playwright/Selenium/Camoufox ma khong sua flow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any

from app.domain.models import Proxy


class BrowserSession(ABC):
    """Mot phien browser dang mo."""

    @abstractmethod
    def goto(self, url: str, wait: float | None = None) -> None: ...

    @abstractmethod
    def current_url(self) -> str: ...

    @abstractmethod
    def wait_for(self, selector: str, timeout: float | None = None) -> Any:
        """Cho element xuat hien. Raise BrowserError neu qua han."""

    @abstractmethod
    def exists(self, selector: str, timeout: float = 0) -> bool: ...

    @abstractmethod
    def type(self, selector: str, text: str, human: bool = True) -> None: ...

    @abstractmethod
    def click(self, selector: str, timeout: float | None = None) -> None: ...

    @abstractmethod
    def text_of(self, selector: str, default: str = "") -> str: ...

    @abstractmethod
    def run_js(self, script: str, *args: Any) -> Any: ...

    @abstractmethod
    def cookies(self) -> dict[str, str]: ...

    @abstractmethod
    def user_agent(self) -> str: ...

    @abstractmethod
    def screenshot(self, path: str) -> str | None: ...

    @abstractmethod
    def switch_to_iframe(self, selector: str) -> None: ...

    @abstractmethod
    def switch_to_main(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...


class BrowserProvider(ABC):
    """Factory tao session."""

    name: str = "base"

    @abstractmethod
    def session(
        self,
        *,
        proxy: Proxy | None = None,
        headless: bool | None = None,
        user_agent: str | None = None,
        profile: str | None = None,
        **kwargs: Any,
    ) -> AbstractContextManager[BrowserSession]:
        """Context manager tra ve BrowserSession, tu dong dong khi thoat."""
