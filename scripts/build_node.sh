#!/usr/bin/env bash
# ============================================================================
#  Build ALL-IN-ONE app standalone (roblox-node) tren LINUX/macOS.
#  Tu lam het: venv -> pip install deps + pyinstaller -> tai Chrome for Testing
#  + extension YesCaptcha -> dong goi. (Tuong duong scripts\build_node.bat cho Win.)
#
#    bash scripts/build_node.sh
#
#  Ket qua: dist/roblox-node/  (copy CA thu muc nay sang may node). PyInstaller
#  khong cross-compile: build tren dung HE DIEU HANH dich.
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

BROWSER=data/browser

# --- 1. venv ---------------------------------------------------------------
if [ ! -x .venv/bin/python ]; then
  echo "[build] Tao virtualenv .venv ..."
  python3 -m venv .venv
fi
PY=.venv/bin/python
PIP=.venv/bin/pip

# --- 2. Cai dependencies ---------------------------------------------------
echo "[build] Cai dependencies ..."
"$PY" -m pip install -U pip
"$PIP" install -e .            # flow-core (app)
"$PIP" install -e node_app    # robloxnode
"$PIP" show pyinstaller >/dev/null 2>&1 || "$PIP" install pyinstaller

# --- 3. Chrome for Testing + extension (neu thieu) -------------------------
have_chrome=""
for c in "$BROWSER"/chrome-*/chrome "$BROWSER"/chrome/chrome "$BROWSER"/chrome-*/chrome.exe; do
  [ -e "$c" ] && have_chrome=1 && break
done
if [ -z "$have_chrome" ]; then
  echo "[build] Tai Chrome for Testing + extension ..."
  "$PY" scripts/fetch_chrome.py
fi
[ -d "$BROWSER/yescaptcha-ext" ] || { echo "[build] Thieu extension, chay: $PY scripts/fetch_chrome.py"; exit 1; }

# --- 4. Dong goi -----------------------------------------------------------
echo "[build] Dong goi PyInstaller ..."
.venv/bin/pyinstaller node_app/roblox-node.spec --noconfirm --clean

echo
echo "[build] XONG -> dist/roblox-node/"
echo "[build] Chay thu: ./dist/roblox-node/roblox-node"
