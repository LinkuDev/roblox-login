"""Adapter Botasaurus -> BrowserSession port.

Chi file nay biet den Botasaurus. Muon doi sang Playwright/Camoufox thi viet
adapter khac va dang ky vao `browser_registry`, flow khong phai sua dong nao.
"""

from __future__ import annotations

import json
import shutil
import stat
import sys
import tempfile
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

from app.core.config import BrowserSettings, get_settings
from app.core.errors import BrowserError
from app.core.logging import get_logger
from app.domain.models import Proxy
from app.domain.ports import BrowserProvider, BrowserSession
from app.providers.browser.base import browser_registry

_ext_log = get_logger("browser.ext")


def _ensure_executable(chrome_path: Path) -> None:
    """Cap lai quyen chay cho Chrome for Testing (PyInstaller datas mat bit +x).

    Chi can khi dong goi; dev thi vo hai. Bo qua tren Windows.
    """
    if sys.platform.startswith("win"):
        return
    cdir = chrome_path.parent
    for t in (chrome_path, cdir / "chrome_sandbox", cdir / "chrome_crashpad_handler"):
        with suppress(OSError):
            if t.exists():
                t.chmod(t.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


class _LoadableExtension:
    """Shim cho botasaurus: no goi `.load(with_command_line_option=False)` va mong
    nhan lai duong dan thu muc extension unpacked (roi tu them --load-extension=)."""

    def __init__(self, path: Path) -> None:
        self._path = str(path)

    def load(self, with_command_line_option: bool = False) -> str:  # noqa: FBT001,FBT002
        return self._path


def _build_config_overrides_js(overrides: dict[str, Any]) -> str:
    """Sinh JS deep-merge overrides vao bien `config` cua extension.

    Cap 1 la dict long (vd funcaptchaConfig) -> Object.assign vao object con; con lai
    gan thang. Gia tri qua json.dumps -> literal JS hop le (true/false/so/chuoi).
    """
    lines: list[str] = []
    for key, val in overrides.items():
        if isinstance(val, dict):
            lines.append(
                f"config[{json.dumps(key)}]=Object.assign(config[{json.dumps(key)}]||{{}},"
                f"{json.dumps(val)});"
            )
        else:
            lines.append(f"config[{json.dumps(key)}]={json.dumps(val)};")
    return "\n".join(lines)


def _prepare_captcha_extension(
    template: Path | None,
    client_key: str | None,
    overrides: dict[str, Any] | None = None,
) -> Path | None:
    """Copy extension TEMPLATE ra thu muc tam va bom config (clientKey + overrides).

    Tra ve thu muc tam da san sang (caller phai xoa khi xong), hoac None neu khong
    co template. Dung ban copy de KHONG dung vao template da commit; profile moi moi
    lan chay -> config.js seed lai chrome.storage.local -> config luon khop app.
    """
    if not template:
        return None
    template = Path(template)
    if not template.exists():
        _ext_log.warning("captcha_extension_missing", path=str(template))
        return None

    runtime = Path(tempfile.mkdtemp(prefix="rlx-yescaptcha-"))
    dest = runtime / "ext"
    shutil.copytree(template, dest)

    merged: dict[str, Any] = dict(overrides or {})
    if client_key:
        merged["clientKey"] = client_key

    if merged:
        cfg = dest / "config.js"
        if not cfg.exists():
            _ext_log.warning("captcha_config_missing", path=str(cfg))
            return dest
        text = cfg.read_text(encoding="utf-8")
        inject = _build_config_overrides_js(merged) + "\n"
        # Chen truoc block seed storage (comment "khong sua" cua extension), fallback
        # chen truoc loi goi chrome.storage.local.get de override an truoc khi luu.
        for anchor in ("// 以下代码请勿修改", "chrome.storage.local.get(['config']"):
            if anchor in text:
                text = text.replace(anchor, inject + anchor, 1)
                cfg.write_text(text, encoding="utf-8")
                break
        else:
            _ext_log.warning("captcha_config_anchor_not_found")
    return dest


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
        """Dien text vao input va DAM BAO gia tri vao that.

        Input cua Roblox la React-controlled: go phim binh thuong co the bi
        React "nuot" neu trang chua hydrate -> form van rong. Nen: focus + clear
        + go phim that, roi VERIFY value; neu van rong thi set qua native setter +
        dispatch input/change (React moi nhan). Rong sau cung -> BrowserError de
        flow fail ro rang, khong submit form rong.
        """
        el = self.wait_for(selector)
        for prep in ("focus", "clear_input"):
            fn = getattr(el, prep, None)
            if callable(fn):
                with suppress(Exception):  # best effort
                    fn()
        try:
            el.send_keys(text)
        except Exception:  # noqa: BLE001 - fallback duoi se lo
            with suppress(Exception):
                self._d.type(selector, text)

        if self._value_of(selector) == text:
            return
        # fallback: set value qua native setter + dispatch event cho React
        self._set_react_value(selector, text)
        if self._value_of(selector) != text:
            raise BrowserError(f"khong dien duoc gia tri vao '{selector}'")

    def _value_of(self, selector: str) -> str | None:
        try:
            return self.run_js(
                f"const el=document.querySelector({json.dumps(selector)});"
                "return el?el.value:null;"
            )
        except BrowserError:
            return None

    def _set_react_value(self, selector: str, text: str) -> None:
        self.run_js(
            f"const el=document.querySelector({json.dumps(selector)});"
            "if(!el)return 'no-el';"
            "el.focus();"
            "const p=el instanceof HTMLTextAreaElement"
            "?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
            "const s=Object.getOwnPropertyDescriptor(p,'value').set;"
            f"s.call(el,{json.dumps(text)});"
            "el.dispatchEvent(new Event('input',{bubbles:true}));"
            "el.dispatchEvent(new Event('change',{bubbles:true}));"
            "return el.value;"
        )

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

    def clear_cookies(self) -> None:
        """Xoa cookie (+ local storage) de phien sau khong dinh account nay."""
        for attr in ("delete_cookies_and_local_storage", "delete_cookies"):
            fn = getattr(self._d, attr, None)
            if callable(fn):
                with suppress(Exception):
                    fn()
                return

    def emulate(
        self,
        width: int,
        height: int,
        mobile: bool = False,
        user_agent: str | None = None,
        scale_factor: float = 1.0,
        client_hints: dict | None = None,
        set_metrics: bool = True,
    ) -> None:
        """Gia lap thiet bi (viewport + UA + Client Hints + touch) qua CDP -> "y het"
        PC hoac dien thoai. KHONG resize cua so OS (dung resize_window cho viec do).

        set_metrics=False: chi doi UA/CH/touch, KHONG ep viewport (de viewport = cua so
        that -> desktop layout hien day du trong cua so rong).
        client_hints: dict (xem constants.*_CLIENT_HINTS) set Sec-CH-UA-* + navigator
        .platform/userAgentData - tranh lo mismatch UA vs client hints.
        """
        from botasaurus_driver import cdp

        if set_metrics:
            with suppress(Exception):
                self._d.run_cdp_command(
                    cdp.emulation.set_device_metrics_override(
                        width=int(width),
                        height=int(height),
                        device_scale_factor=float(scale_factor),
                        mobile=bool(mobile),
                    )
                )
        with suppress(Exception):
            self._d.run_cdp_command(cdp.emulation.set_touch_emulation_enabled(enabled=bool(mobile)))
        if user_agent:
            meta = None
            nav_platform = None
            if client_hints:
                ch = client_hints
                brands = [
                    cdp.emulation.UserAgentBrandVersion(brand=b, version=v)
                    for b, v in ch.get("brands", [])
                ]
                full_list = [
                    cdp.emulation.UserAgentBrandVersion(brand=b, version=ch.get("full_version", ""))
                    for b, _ in ch.get("brands", [])
                ]
                meta = cdp.emulation.UserAgentMetadata(
                    platform=ch.get("platform", ""),
                    platform_version=ch.get("platform_version", ""),
                    architecture=ch.get("architecture", ""),
                    model=ch.get("model", ""),
                    mobile=ch.get("mobile", mobile),
                    brands=brands,
                    full_version_list=full_list,
                    full_version=ch.get("full_version"),
                    bitness=ch.get("bitness", ""),
                )
                nav_platform = ch.get("nav_platform")
            with suppress(Exception):
                self._d.run_cdp_command(
                    cdp.emulation.set_user_agent_override(
                        user_agent=user_agent,
                        platform=nav_platform,
                        user_agent_metadata=meta,
                    )
                )

    def reload(self) -> None:
        with suppress(Exception):
            self._d.reload()

    def resize_window(
        self, width: int, height: int, x: int | None = None, y: int | None = None
    ) -> None:
        """Resize (va tuy chon REPOSITION) CUA SO OS that qua CDP Browser.setWindowBounds.
        Login = rong (desktop, maximize). /not-approved = hep (mobile) + dat vao o luoi
        (x, y) de cac phien khong de len nhau."""
        from botasaurus_driver import cdp

        with suppress(Exception):
            window_id, _ = self._d.run_cdp_command(cdp.browser.get_window_for_target())
            # NORMAL truoc (bo maximize neu dang maximize) roi moi set bounds
            self._d.run_cdp_command(
                cdp.browser.set_window_bounds(
                    window_id, cdp.browser.Bounds(window_state=cdp.browser.WindowState.NORMAL)
                )
            )
            bounds_kw: dict[str, int] = {"width": int(width), "height": int(height)}
            if x is not None and y is not None:
                bounds_kw["left"] = int(x)
                bounds_kw["top"] = int(y)
            self._d.run_cdp_command(
                cdp.browser.set_window_bounds(window_id, cdp.browser.Bounds(**bounds_kw))
            )

    def maximize_window(self) -> None:
        """Phong to cua so full man hinh (login = trai nghiem PC fullwidth)."""
        from botasaurus_driver import cdp

        with suppress(Exception):
            window_id, _ = self._d.run_cdp_command(cdp.browser.get_window_for_target())
            self._d.run_cdp_command(
                cdp.browser.set_window_bounds(
                    window_id,
                    cdp.browser.Bounds(window_state=cdp.browser.WindowState.MAXIMIZED),
                )
            )

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
        window_position: tuple[int, int] | None = None,
        window_size: tuple[int, int] | None = None,
        **kwargs: Any,
    ):
        try:
            # Dung botasaurus_driver truc tiep (khong qua goi 'botasaurus' full -> tranh
            # phu thuoc javascript_fixes/Node.js khi dong goi PyInstaller).
            from botasaurus_driver import Driver
        except ImportError as exc:  # pragma: no cover
            raise BrowserError(
                "chua cai botasaurus-driver. Chay: pip install botasaurus-driver"
            ) from exc

        want_headless = self.settings.headless if headless is None else headless
        opts: dict[str, Any] = {
            "headless": want_headless,
            # Botasaurus muon (w, h); settings luu chuoi "w,h" nen dung .window.
            # window_size override (vd tiling phone thu nho) -> uu tien.
            "window_size": window_size or self.settings.window,
        }
        if proxy:
            opts["proxy"] = proxy.url
        if ua := (user_agent or self.settings.user_agent):
            opts["user_agent"] = ua
        if profile:
            opts["profile"] = profile
        # Vi tri cua so tren man hinh (tiling: xep khong de nhau) qua chrome arg.
        if window_position is not None:
            x, y = window_position
            opts.setdefault("arguments", []).append(f"--window-position={x},{y}")

        # Nhan = Chrome for Testing (khong dung Chrome goc) neu co san.
        chrome_path = self.settings.chrome_executable_path
        if chrome_path and Path(chrome_path).exists():
            if getattr(sys, "frozen", False):
                _ensure_executable(Path(chrome_path))
            opts["chrome_executable_path"] = str(chrome_path)

        # Extension YesCaptcha: copy template -> temp + bom clientKey tu config
        # -> tu giai captcha in-page (khong dung API). Extension chi chay headful.
        ext_runtime = _prepare_captcha_extension(
            self.settings.captcha_extension_dir,
            self.settings.captcha_client_key,
            self.settings.captcha_config_overrides,
        )
        if ext_runtime is not None:
            opts["extensions"] = [_LoadableExtension(ext_runtime)]
            opts["headless"] = False  # extension khong hoat dong o headless cu

        opts.update(kwargs)
        # cho phep override window_size bang chuoi "w,h" -> chuan hoa ve (w, h)
        if isinstance(opts.get("window_size"), str):
            w, _, h = opts["window_size"].partition(",")
            opts["window_size"] = (int(w), int(h))

        driver = Driver(**opts)
        session = BotasaurusSession(driver, self.settings)
        try:
            yield session
        finally:
            session.close()
            if ext_runtime is not None:
                # ext_runtime = <tmp>/ext -> xoa ca thu muc tam goc
                shutil.rmtree(ext_runtime.parent, ignore_errors=True)
