"""Chay web UI cau hinh node roi mo trong 1 cua so Chrome (--app).

  python -m robloxnode        # mo app cau hinh
"""

from __future__ import annotations

import contextlib
import shutil
import socket
import subprocess
import tempfile
import threading
import time

import uvicorn

from robloxnode.webapp import build_app


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
        return subprocess.Popen(
            [
                chrome,
                f"--app={url}",
                f"--user-data-dir={profile}",
                "--window-size=440,720",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
    import webbrowser

    webbrowser.open(url)
    return None


def _wait_up(port: int, tries: int = 100) -> None:
    for _ in range(tries):
        with contextlib.suppress(OSError), socket.create_connection(
            ("127.0.0.1", port), timeout=0.2
        ):
            return
        time.sleep(0.1)


def main() -> None:
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(build_app(), host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_up(port)

    url = f"http://127.0.0.1:{port}"
    print(f"Node config UI: {url}")
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


if __name__ == "__main__":
    main()
