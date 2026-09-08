"""Gui nhat ky (log) len he thong ngoai qua POST /api/logs.

Fire-and-forget (chay o thread rieng, nuot loi) -> khong bao gio lam cham/chet node
du server log co down. URL lay tu NodeConfig.log_url (rong = tat).
"""

from __future__ import annotations

import json
import os
import platform
import socket
import threading
import urllib.request


def post_log(url: str, payload: dict, timeout: float = 8.0) -> None:
    """POST payload (JSON) len url. Khong chan luong chinh, loi thi bo qua."""
    if not url:
        return

    def _send() -> None:
        try:
            data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}, method="POST"
            )
            urllib.request.urlopen(req, timeout=timeout).close()
        except Exception:  # noqa: BLE001 - log best-effort, khong duoc lam sap node
            pass

    threading.Thread(target=_send, daemon=True).start()


def pc_info(node_name: str = "") -> dict:
    """Thong tin co ban cua may (payload luc mo node)."""
    info: dict = {
        "node_name": node_name,
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    try:
        import psutil

        vm = psutil.virtual_memory()
        info["ram_total_gb"] = round(vm.total / (1024**3), 1)
        info["ram_percent"] = vm.percent
    except Exception:  # noqa: BLE001 - psutil co the thieu
        pass
    try:
        # IP LAN (best-effort, khong ra internet)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["local_ip"] = s.getsockname()[0]
        s.close()
    except Exception:  # noqa: BLE001
        pass
    return info
