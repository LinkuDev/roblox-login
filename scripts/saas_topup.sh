#!/usr/bin/env bash
# Nap diem cho 1 user (dev helper). Dung khi POINT_SIGNUP_BONUS=0.
#   scripts/saas_topup.sh <email> <so_diem>
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH=src
.venv/bin/python - "$@" <<'PY'
import sys
email, amount = sys.argv[1], int(sys.argv[2])
from app.db.session import session_scope
from app.db.repositories import UserRepository
from app.modules.billing import BillingService
with session_scope() as s:
    u = UserRepository(s).by_email(email)
    if not u:
        print(f"khong tim thay user {email} (dang ky truoc da)"); sys.exit(1)
    bal = BillingService(s).topup(u.id, amount, note="dev topup")
    print(f"OK: {email} -> {bal} diem")
PY
