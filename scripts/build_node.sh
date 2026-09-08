#!/usr/bin/env bash
# Build app standalone (roblox-node) kem Chrome for Testing + extension YesCaptcha.
# Chay tren dung HE DIEU HANH dich (PyInstaller khong cross-compile).
#
#   bash scripts/build_node.sh
#
# Ket qua: dist/roblox-node/  (thu muc chay - onedir). Copy ca thu muc nay sang may node.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv/bin/python
PIP=.venv/bin/pip
BROWSER=data/browser

# 1. Kiem tra nhan Chrome + extension; thieu thi tai
if ! ls "$BROWSER"/chrome-*/chrome "$BROWSER"/chrome/chrome "$BROWSER"/chrome-*/chrome.exe 2>/dev/null | head -1 >/dev/null; then
  echo "[build] Thieu Chrome for Testing -> tai..."
  "$PY" scripts/fetch_chrome.py
fi
[ -d "$BROWSER/yescaptcha-ext" ] || { echo "[build] Thieu extension, chay: $PY scripts/fetch_chrome.py"; exit 1; }

# 2. PyInstaller
"$PIP" show pyinstaller >/dev/null 2>&1 || "$PIP" install pyinstaller

# 3. Build
.venv/bin/pyinstaller node_app/roblox-node.spec --noconfirm --clean

echo
echo "[build] Xong -> dist/roblox-node/"
echo "[build] Chay thu: ./dist/roblox-node/roblox-node"
