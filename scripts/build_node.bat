@echo off
REM ============================================================================
REM  Build ALL-IN-ONE app standalone (roblox-node) tren WINDOWS.
REM  Tu lam het: tao venv -> pip install deps + pyinstaller -> tai Chrome for
REM  Testing (win64) + extension YesCaptcha -> dong goi.
REM
REM  Cach chay: double-click file nay, hoac: scripts\build_node.bat
REM  Ket qua:   dist\roblox-node\roblox-node.exe  (copy CA thu muc dist\roblox-node)
REM
REM  Yeu cau: da cai Python 3.11+ (co trong PATH).
REM ============================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

REM --- 1. Python ---------------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
  echo [build] Khong tim thay "python" trong PATH. Cai Python 3.11+ va tick "Add to PATH".
  pause & exit /b 1
)

REM --- 2. venv -----------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo [build] Tao virtualenv .venv ...
  python -m venv .venv || (echo [build] Loi tao venv & pause & exit /b 1)
)
set "PY=.venv\Scripts\python.exe"
set "PIP=.venv\Scripts\pip.exe"

REM --- 3. Cai dependencies -----------------------------------------------------
echo [build] Cai dependencies (co the mat vai phut lan dau)...
"%PY%" -m pip install -U pip                 || (echo [build] pip upgrade loi & pause & exit /b 1)
"%PIP%" install -e .                         || (echo [build] cai flow-core loi   & pause & exit /b 1)
"%PIP%" install -e node_app                  || (echo [build] cai robloxnode loi  & pause & exit /b 1)
"%PIP%" install pyinstaller                  || (echo [build] cai pyinstaller loi & pause & exit /b 1)

REM --- 4. Chrome for Testing + extension (neu thieu) ---------------------------
if not exist "data\browser\chrome-win64\chrome.exe" (
  echo [build] Tai Chrome for Testing ^(win64^) + extension YesCaptcha ...
  "%PY%" scripts\fetch_chrome.py             || (echo [build] tai Chrome/extension loi & pause & exit /b 1)
)
if not exist "data\browser\yescaptcha-ext" (
  echo [build] Thieu extension. Chay: %PY% scripts\fetch_chrome.py
  pause & exit /b 1
)

REM --- 5. Dong goi -------------------------------------------------------------
echo [build] Dong goi PyInstaller ...
".venv\Scripts\pyinstaller.exe" node_app\roblox-node.spec --noconfirm --clean
if errorlevel 1 (echo [build] PyInstaller loi & pause & exit /b 1)

echo.
echo [build] XONG -^> dist\roblox-node\roblox-node.exe
echo [build] Copy ca thu muc dist\roblox-node sang may node de chay.
endlocal
pause
