@echo off
REM ============================================================================
REM  BUILD ALL-IN-ONE (Windows) - roblox-node.exe
REM  Tu lam HET tu may trang:
REM    - Cai Python 3.11.9 (neu chua co)      - silent
REM    - Tao venv + pip deps + pyinstaller
REM    - Tai Chrome for Testing (win64) + extension YesCaptcha
REM    - Dong goi -> dist\roblox-node\roblox-node.exe
REM
REM  KHONG can Node.js: proxy auth do 1 extension MV3 tu lo (in-browser).
REM  Chay: double-click, hoac  scripts\build_node.bat
REM  Yeu cau: Windows 10 1803+ (co san curl). Chay bang quyen thuong la du.
REM ============================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

set "PYVER=3.11.9"

REM --- 1. Python 3.11 ----------------------------------------------------------
set "PY=python"
python --version 2>nul | findstr /b "Python 3.11" >nul
if not errorlevel 1 goto :py_ok
echo [build] Chua co Python 3.11 -^> tai + cai %PYVER% (silent)...
set "PYINST=%TEMP%\python-%PYVER%-amd64.exe"
curl -L -o "!PYINST!" "https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-amd64.exe" || (echo [build] Tai Python loi & pause & exit /b 1)
"!PYINST!" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_launcher=1
set "PY=%LocalAppData%\Programs\Python\Python311\python.exe"
if not exist "!PY!" set "PY=%ProgramFiles%\Python311\python.exe"
:py_ok
"!PY!" --version || (echo [build] Python khong chay & pause & exit /b 1)

REM --- 2. venv ----------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo [build] Tao virtualenv .venv ...
  "!PY!" -m venv .venv || (echo [build] Loi tao venv & pause & exit /b 1)
)
set "VPY=.venv\Scripts\python.exe"
set "PIP=.venv\Scripts\pip.exe"

REM --- 3. Dependencies --------------------------------------------------------
echo [build] Cai dependencies (lan dau vai phut)...
"%VPY%" -m pip install -U pip                 || (echo [build] pip upgrade loi & pause & exit /b 1)
"%PIP%" install -e .                          || (echo [build] cai flow-core loi   & pause & exit /b 1)
"%PIP%" install -e node_app                   || (echo [build] cai robloxnode loi  & pause & exit /b 1)
"%PIP%" install pyinstaller                   || (echo [build] cai pyinstaller loi & pause & exit /b 1)

REM --- 4. Chrome for Testing + extension --------------------------------------
if not exist "data\browser\chrome-win64\chrome.exe" (
  echo [build] Tai Chrome for Testing ^(win64^) + extension YesCaptcha ...
  "%VPY%" scripts\fetch_chrome.py             || (echo [build] tai Chrome/extension loi & pause & exit /b 1)
)
if not exist "data\browser\yescaptcha-ext" (
  echo [build] Thieu extension yescaptcha-ext. Chay: %VPY% scripts\fetch_chrome.py
  pause & exit /b 1
)

REM --- 5. Dong goi ------------------------------------------------------------
echo [build] Don dist cu (tat app dang chay neu co)...
taskkill /F /IM roblox-node.exe >nul 2>nul
if exist "dist\roblox-node" rmdir /s /q "dist\roblox-node"

echo [build] Dong goi PyInstaller ...
".venv\Scripts\pyinstaller.exe" node_app\roblox-node.spec --noconfirm --clean
if errorlevel 1 (echo [build] PyInstaller loi & pause & exit /b 1)

echo.
echo [build] XONG -^> dist\roblox-node\roblox-node.exe
echo [build] Copy CA thu muc dist\roblox-node sang may node de chay (KHONG can Node.js).
endlocal
pause
