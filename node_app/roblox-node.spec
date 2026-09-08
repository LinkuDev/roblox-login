# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: dong goi app standalone (robloxnode) KEM Chrome for Testing +
extension YesCaptcha ben trong.

    .venv/bin/pyinstaller node_app/roblox-node.spec --noconfirm --clean

Build ONEDIR (khuyen nghi vi Chrome ~300MB) -> dist/roblox-node/ (thu muc chay).
LUU Y: PyInstaller KHONG cross-compile. Phai build tren dung HE DIEU HANH dich, va
data/browser phai chua Chrome for Testing dung nen tang (chay scripts/fetch_chrome.py).
"""

from pathlib import Path

from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).resolve().parent  # spec o node_app/ -> parent = repo root
BROWSER = ROOT / "data" / "browser"

datas: list = []
binaries: list = []
hiddenimports: list = []

# Chi gom botasaurus_driver (Driver) + uvicorn. KHONG gom goi 'botasaurus' full vi
# no keo 'javascript_fixes' -> doi Node.js luc import -> vo PyInstaller.
for pkg in ("botasaurus_driver", "uvicorn"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# service/provider/step dang ky qua import dong -> ep gom het
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("robloxnode")

# Chrome for Testing + extension -> giu nguyen cay thu muc duoi browser/ trong bundle
trees: list = []
for sub in ("chrome", "chrome-linux64", "chrome-win64", "chrome-mac-x64", "chrome-mac-arm64"):
    p = BROWSER / sub
    if p.exists():
        trees.append(Tree(str(p), prefix=f"browser/{sub}"))
ext = BROWSER / "yescaptcha-ext"
if ext.exists():
    trees.append(Tree(str(ext), prefix="browser/yescaptcha-ext"))

a = Analysis(
    [str(ROOT / "node_app" / "robloxnode" / "__main__.py")],
    pathex=[str(ROOT / "src"), str(ROOT / "node_app")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # 'botasaurus' full + 'javascript_fixes' can Node.js -> loai khoi bundle
    # (flow chi dung 'botasaurus_driver').
    excludes=["botasaurus", "javascript_fixes"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="roblox-node",
    console=True,          # doi False neu muon an cua so console
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    *trees,
    strip=False,
    upx=False,             # UPX co the lam Chrome/AV bao dong -> tat
    name="roblox-node",
)
