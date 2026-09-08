"""ResultStore: DB local cua node - ghi ket qua moi record ra JSONL (append).

Cover CA 2 case:
  - success -> status=success, luu .ROBLOSECURITY
  - failed  -> status=failed, luu error_code + reason (vd need_mobile_app)

Mac dinh ghi canh config: ~/.roblox-node/results.jsonl (doi bang RLX_NODE_RESULTS).
Sau nay thay bang WsPool.report toi SaaS ma agent khong doi.
"""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import suppress
from pathlib import Path

from robloxnode.config import default_config_path
from robloxnode.pool import Record


def default_results_path() -> Path:
    env = os.environ.get("RLX_NODE_RESULTS")
    if env:
        return Path(env)
    return default_config_path().parent / "results.jsonl"


class ResultStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else default_results_path()
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: Record, result: dict) -> None:
        cookies = result.get("cookies") or {}
        ok = bool(result.get("success"))
        row = {
            "ts": round(time.time(), 3),
            "id": record.id,
            "username": record.username,
            "status": "success" if ok else "failed",
            "error": result.get("error"),
            "reason": result.get("reason"),
            "roblosecurity": cookies.get(".ROBLOSECURITY", "") if ok else "",
        }
        line = json.dumps(row, ensure_ascii=False)
        with self._lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def load(self, limit: int = 300) -> dict:
        """Doc ket qua cho UI: summary (dem theo status/loi) + rows moi nhat truoc."""
        rows: list[dict] = []
        if self.path.exists():
            with self._lock:
                lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        summary = {"total": len(rows), "success": 0, "failed": 0, "by_error": {}}
        for r in rows:
            if r.get("status") == "success":
                summary["success"] += 1
            else:
                summary["failed"] += 1
                err = r.get("error") or "unknown"
                summary["by_error"][err] = summary["by_error"].get(err, 0) + 1
        return {"summary": summary, "rows": list(reversed(rows))[:limit]}

    def clear(self) -> None:
        with self._lock, suppress(OSError):
            self.path.unlink()
