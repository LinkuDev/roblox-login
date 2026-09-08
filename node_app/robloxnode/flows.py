"""run_flow: xu ly 1 record = 1 browser + auto vai thao tac -> tra ket qua.

Trc mat la STUB (gia lap thoi gian + ket qua) de thay vong lap agent chay that.
Sau khi tach flow-core, thay bang: run_service("roblox.login", cred, ...) that.
"""

from __future__ import annotations

import random
import time

from robloxnode.pool import Record


def stub_flow(record: Record, placement: dict | None = None, proxy: str | None = None) -> dict:
    """Gia lap 1 flow: ton ~1.5-4s, ~85% thanh cong. (placement bo qua o stub)"""
    time.sleep(random.uniform(1.5, 4.0))
    ok = random.random() > 0.15
    if ok:
        return {"success": True, "cookies": {".ROBLOSECURITY": "stub"}, "error": None}
    return {"success": False, "error": "invalid_credentials"}
