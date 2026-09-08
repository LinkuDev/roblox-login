#!/usr/bin/env python
"""Tai Chrome for Testing (dung nen tang hien tai) + extension YesCaptcha vao
data/browser/ - de dev va de build standalone.

    .venv/bin/python scripts/fetch_chrome.py

Tao:
  data/browser/<chrome-...>/chrome[.exe]     # nhan trinh duyet
  data/browser/yescaptcha-ext/               # extension unpacked (TEMPLATE, key rong)
"""
from __future__ import annotations

import io
import json
import platform
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BROWSER = ROOT / "data" / "browser"
CFT_JSON = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
YESCAPTCHA_ID = "jiofmdifioeejeilfkpegipdjiopiekl"


def _platform_key() -> str:
    if sys.platform.startswith("win"):
        return "win64"
    if sys.platform == "darwin":
        return "mac-arm64" if platform.machine().lower() in ("arm64", "aarch64") else "mac-x64"
    return "linux64"


def _download(url: str, timeout: int = 900) -> bytes:
    print(f"  tai {url}")
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310
        return r.read()


def fetch_chrome() -> None:
    plat = _platform_key()
    data = json.loads(_download(CFT_JSON, timeout=30))
    st = data["channels"]["Stable"]
    url = next(x["url"] for x in st["downloads"]["chrome"] if x["platform"] == plat)
    print(f"Chrome for Testing {st['version']} ({plat})")
    blob = _download(url)
    BROWSER.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        z.extractall(BROWSER)  # tao thu muc chrome-<plat>/
    # cap quyen chay tren unix
    if not sys.platform.startswith("win"):
        for chrome in BROWSER.glob(f"chrome-{plat}/chrome"):
            chrome.chmod(0o755)
    print(f"  -> {BROWSER}/chrome-{plat}/")


def fetch_extension() -> None:
    url = (
        "https://clients2.google.com/service/update2/crx?response=redirect"
        "&acceptformat=crx2,crx3&prodversion=120.0&x=id%3D" + YESCAPTCHA_ID + "%26uc"
    )
    print("Extension YesCaptcha")
    blob = _download(url, timeout=120)
    dest = BROWSER / "yescaptcha-ext"
    dest.mkdir(parents=True, exist_ok=True)
    # CRX = header + zip; ZipFile tu tim central directory nen mo truc tiep duoc
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        z.extractall(dest)
    print(f"  -> {dest}/ (clientKey set luc chay tu config app)")


def main() -> None:
    fetch_chrome()
    fetch_extension()
    print("Xong. Gio co the: .venv/bin/pyinstaller node_app/roblox-node.spec --noconfirm")


if __name__ == "__main__":
    main()
