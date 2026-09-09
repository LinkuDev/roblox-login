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

    def clear_cookies(self) -> None:  # noqa: B027 - hook tuy chon, mac dinh no-op
        """Xoa cookie phien hien tai (provider override neu ho tro)."""

    def is_page_loading(self) -> bool:  # noqa: B027 - hook tuy chon
        """True neu trang dang tai (readyState != 'complete'). Provider override neu ho tro."""
        return False

    def wait_page_loaded(self, timeout: float = 30.0, poll: float = 0.5) -> bool:  # noqa: B027
        """Cho toi khi trang tai xong (readyState == 'complete'). Provider override."""
        return True

    def emulate(  # noqa: B027 - hook tuy chon, mac dinh no-op
        self,
        width: int,
        height: int,
        mobile: bool = False,
        user_agent: str | None = None,
        scale_factor: float = 1.0,
        client_hints: dict | None = None,
    ) -> None:
        """Gia lap thiet bi (viewport + UA + Client Hints). Provider override neu ho tro."""

    def reload(self) -> None:  # noqa: B027 - hook tuy chon, mac dinh no-op
        """Tai lai trang hien tai (provider override neu ho tro)."""

    def resize_window(  # noqa: B027
        self, width: int, height: int, x: int | None = None, y: int | None = None
    ) -> None:
        """Resize (va tuy chon reposition den x,y) cua so OS that (provider override)."""

    def maximize_window(self) -> None:  # noqa: B027 - hook tuy chon, mac dinh no-op
        """Phong to cua so full man hinh (provider override neu ho tro)."""

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
