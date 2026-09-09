"""RemotePool: node keo record tu SaaS pool qua HTTP (claim/report).

Implement cung interface PoolClient (has_work/claim/report/pending_count) nhu
LocalPool -> NodeAgent khong doi. Auth bang X-API-Key (pool_token). Doc lap voi
transport: sau nay doi WSS chi viet class khac.
"""

from __future__ import annotations

import json
import time
import urllib.request

from robloxnode.pool import Record


class RemotePool:
    def __init__(
        self, base_url: str, token: str, node_id: str = "node", lease_ttl: int = 240
    ) -> None:
        self.base = base_url.rstrip("/")
        self.token = token
        self.node_id = node_id
        # Lease TTL (giay): record giu bao lau truoc khi bi reclaim neu KHONG heartbeat.
        # Agent heartbeat dinh ky (< lease_ttl) -> node song thi khong bi cuop; node chet
        # thi sau lease_ttl record duoc reclaim. Nen > khoang heartbeat cua agent.
        self.lease_ttl = lease_ttl

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
            code, data = self._req(
                "POST",
                "/api/v1/pool/claim",
                {"node_id": self.node_id, "ttl_seconds": self.lease_ttl},
            )
        except Exception:  # noqa: BLE001 - SaaS down/mang loi -> coi nhu khong co viec
            return None
        if code == 204 or not data:
            return None
        return Record(
            id=data["record_id"],
            username=data["username"],
            password=data["password"],
            totp_secret=data.get("totp_secret"),   # SaaS tra kem -> acc 2FA login duoc
            email=data.get("email"),
        )

    def report(self, record_id: str, result: dict) -> None:
        # RETRY: report mang gia tri lon (cookie) -> mat vi loi mang thoang qua thi record
        # ket 'running' -> bi reclaim + chay lai (phi cong). Thu 3 lan, backoff.
        for attempt in range(3):
            try:
                self._req(
                    "POST",
                    "/api/v1/pool/report",
                    {"record_id": record_id, "result": result, "node_id": self.node_id},
                )
                return
            except Exception:  # noqa: BLE001 - thu lai; ket qua van con o ResultStore local
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))

    def heartbeat(self, record_id: str) -> bool:
        """Gia han lease record dang chay. False = da mat lease (bi reclaim/da report)."""
        try:
            _, data = self._req(
                "POST",
                "/api/v1/pool/heartbeat",
                {"record_id": record_id, "node_id": self.node_id, "ttl_seconds": self.lease_ttl},
                timeout=10.0,
            )
            return bool((data or {}).get("ok"))
        except Exception:  # noqa: BLE001 - mang loi -> coi nhu chua mat, cu chay tiep
            return True

    def pending_count(self) -> int:
        try:
            _, data = self._req("GET", "/api/v1/pool/stats")
            return int((data or {}).get("queued", 0))
        except Exception:  # noqa: BLE001
            return 0
