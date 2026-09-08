"""RemotePool: node keo record tu SaaS pool qua HTTP (claim/report).

Implement cung interface PoolClient (has_work/claim/report/pending_count) nhu
LocalPool -> NodeAgent khong doi. Auth bang X-API-Key (pool_token). Doc lap voi
transport: sau nay doi WSS chi viet class khac.
"""

from __future__ import annotations

import json
import urllib.request

from robloxnode.pool import Record


class RemotePool:
    def __init__(self, base_url: str, token: str, node_id: str = "node") -> None:
        self.base = base_url.rstrip("/")
        self.token = token
        self.node_id = node_id

    # --- HTTP -------------------------------------------------------------
    def _req(self, method: str, path: str, body: dict | None = None, timeout: float = 15.0):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "X-API-Key": self.token},
        )
        resp = urllib.request.urlopen(req, timeout=timeout)
        code = resp.getcode()
        raw = resp.read().decode() or ""
        resp.close()
        return code, (json.loads(raw) if raw else None)

    # --- PoolClient interface --------------------------------------------
    def has_work(self) -> bool:
        # De claim quyet dinh (claim rong -> None -> agent ngu). Tra True cho don gian.
        return True

    def claim(self) -> Record | None:
        try:
            code, data = self._req("POST", "/api/v1/pool/claim", {"node_id": self.node_id})
        except Exception:  # noqa: BLE001 - SaaS down/mang loi -> coi nhu khong co viec
            return None
        if code == 204 or not data:
            return None
        return Record(id=data["record_id"], username=data["username"], password=data["password"])

    def report(self, record_id: str, result: dict) -> None:
        try:
            self._req(
                "POST",
                "/api/v1/pool/report",
                {"record_id": record_id, "result": result, "node_id": self.node_id},
            )
        except Exception:  # noqa: BLE001 - report loi khong duoc lam chet slot
            pass

    def pending_count(self) -> int:
        try:
            _, data = self._req("GET", "/api/v1/pool/stats")
            return int((data or {}).get("queued", 0))
        except Exception:  # noqa: BLE001
            return 0
