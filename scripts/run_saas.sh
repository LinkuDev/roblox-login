#!/usr/bin/env bash
# Chay SaaS web (dev). Doc cau hinh tu .env (APP_ADMIN_EMAILS, DATABASE_URL...).
#   scripts/run_saas.sh
set -e
cd "$(dirname "$0")/.."

# venv + deps (fastapi/uvicorn/... tu pyproject)
[ -d .venv ] || python3 -m venv .venv
if ! .venv/bin/python -c "import uvicorn,fastapi" 2>/dev/null; then
  echo "[saas] Cai dependencies (lan dau)..."
  .venv/bin/pip install -q -U pip
  .venv/bin/pip install -q -e ".[postgres]" || .venv/bin/pip install -q -e .
fi

export PYTHONPATH=src
PORT="${PORT:-8000}"
ADMIN=$(grep -E '^APP_ADMIN_EMAILS=' .env 2>/dev/null | cut -d= -f2)

echo "============================================================"
echo " SaaS web:  http://localhost:$PORT"
echo " Admin:     ${ADMIN:-'(chua set APP_ADMIN_EMAILS trong .env)'}"
echo "   1) Mo web -> Dang ky bang email admin o tren -> thanh admin"
echo "   2) Nap diem cho admin de test order:"
echo "        scripts/saas_topup.sh ${ADMIN:-admin@mail} 100"
echo "   3) Tao order (dan tk:pass) -> tru diem -> pool"
echo "   4) 'Tao API key' -> dung lam Pool token cho node"
echo "============================================================"
exec .venv/bin/uvicorn app.main:api --app-dir src --reload --port "$PORT"
