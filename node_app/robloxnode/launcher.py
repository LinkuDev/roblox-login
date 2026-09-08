"""Chay web UI cau hinh node roi mo trong 1 cua so Chrome (--app).

  python -m robloxnode        # mo app cau hinh
"""

from __future__ import annotations

import atexit
import contextlib
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

import uvicorn

from robloxnode.webapp import build_app


def _our_chrome_dir() -> str | None:
    """Thu muc binary Chrome for Testing di kem (de nhan dien process cua MINH)."""
    with contextlib.suppress(Exception):
        from app.core.config import default_chrome_path

        return str(default_chrome_path().parent).lower()
    return None


_CLEANED = False


def cleanup_chrome() -> None:
    """Kill TAT CA Chrome for Testing do app nay spawn (UI + cac flow) khi dong app,
    tranh leak memory. Match theo path binary bundle -> KHONG dung Chrome he thong.
    Idempotent (chi chay 1 lan)."""
    global _CLEANED
    if _CLEANED:
        return
    _CLEANED = True
    cdir = _our_chrome_dir()
    if not cdir:
        return
    try:
        import psutil
    except Exception:  # noqa: BLE001
        return
    me = os.getpid()

    def _is_ours(p) -> bool:
        try:
            exe = (p.info.get("exe") or "").lower()
            cmd = " ".join(p.info.get("cmdline") or []).lower()
            return p.info["pid"] != me and (exe.startswith(cdir) or cdir in cmd)
        except Exception:  # noqa: BLE001
            return False

    killed = 0
    # Chrome hay respawn helper -> quet nhieu pass cho sach han
    for _ in range(4):
        procs = [p for p in psutil.process_iter(["pid", "exe", "cmdline"]) if _is_ours(p)]
        if not procs:
            break
        for p in procs:
            with contextlib.suppress(Exception):
                p.kill()
                killed += 1
        time.sleep(0.3)
    # don thu muc tam cua app (UI profile + extension da materialize)
    with contextlib.suppress(Exception):
        tmp = tempfile.gettempdir()
        for name in os.listdir(tmp):
            if name.startswith(("rlx-node-ui-", "rlx-yescaptcha-")):
                shutil.rmtree(os.path.join(tmp, name), ignore_errors=True)
    if killed:
        print(f"[cleanup] da tat {killed} tien trinh Chrome for Testing")


def _install_cleanup_hooks() -> None:
    """Dam bao cleanup_chrome() chay o MOI kieu dong: exit thuong, Ctrl+C, SIGTERM,
    va bam X cua so console tren Windows."""
    atexit.register(cleanup_chrome)
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(Exception):
            signal.signal(sig, lambda *_: (cleanup_chrome(), sys.exit(0)))
    if sys.platform.startswith("win"):
        _install_win_console_handler()


_win_handler_ref = None  # giu tham chieu callback khoi bi GC


def _install_win_console_handler() -> None:
    global _win_handler_ref
    with contextlib.suppress(Exception):
        import ctypes

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)
        def handler(ctrl_type: int) -> bool:  # noqa: ARG001
            cleanup_chrome()
            return False  # cho handler mac dinh terminate tiep

        _win_handler_ref = handler
        ctypes.windll.kernel32.SetConsoleCtrlHandler(handler, True)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _find_chrome() -> str | None:
    # Uu tien Chrome for Testing di kem (bundle) -> app that su standalone,
    # khong phu thuoc Chrome he thong.
    try:
        from app.core.config import default_chrome_path

        p = default_chrome_path()
        if p.exists():
            with contextlib.suppress(OSError):
                import stat

                p.chmod(p.stat().st_mode | stat.S_IXUSR)
            return str(p)
    except Exception:  # flow-core chua co (dev thuan node) -> fallback he thong
        pass
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _open_window(url: str) -> subprocess.Popen | None:
    chrome = _find_chrome()
    if chrome:
        profile = tempfile.mkdtemp(prefix="rlx-node-ui-")
        # Mo cua so THUONG (URL positional) thay vi --app: CfT --app voi http://IP:port
        # hay bi trang. Cua so thuong load on dinh (co address bar - chap nhan duoc).
        args = [
            chrome,
            "--new-window",
            f"--user-data-dir={profile}",
            "--window-size=440,760",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-search-engine-choice-screen",
            url,
        ]
        print(f"[ui] mo cua so: {chrome}\n[ui]   url={url}")
        return subprocess.Popen(args)
    import webbrowser

    print(f"[ui] khong thay chrome -> mo trinh duyet mac dinh: {url}")
    webbrowser.open(url)
    return None


def _wait_up(port: int, tries: int = 200) -> bool:
    """Doi den khi server tra HTTP 200 that (khong chi TCP) -> tranh mo cua so
    truoc khi server san sang khien trang trang."""
    url = f"http://127.0.0.1:{port}/"
    for _ in range(tries):
        with contextlib.suppress(Exception), urllib.request.urlopen(url, timeout=0.4) as r:  # noqa: S310
            if getattr(r, "status", 200) == 200:
                return True
        time.sleep(0.1)
    return False


def main() -> None:
    _install_cleanup_hooks()   # dong app -> kill sach Chrome cua minh (tranh leak)
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            build_app(),
            host="127.0.0.1",
            port=port,
            log_level="warning",
            # Ep implementation THUAN PYTHON de dong goi PyInstaller chay duoc:
            # httptools/websockets/uvloop la goi C ngoai, khong bundle -> request
            # rot vao hu khong (trang trang) du port da mo.
            loop="asyncio",
            http="h11",
            ws="none",
            lifespan="off",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    print(f"Node config UI: {url}")
    if _wait_up(port):
        print("[ui] server san sang (HTTP 200)")
    else:
        print("[ui] CANH BAO: server chua tra 200, van thu mo cua so")
    proc = _open_window(url)
    try:
        if proc is not None:
            proc.wait()             # app song cung cua so
        else:
            while thread.is_alive():
                time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.should_exit = True
        cleanup_chrome()   # tat het Chrome for Testing con song


if __name__ == "__main__":
    main()
