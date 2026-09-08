"""Cau hinh cua 1 node (app standalone). Luu ra JSON de app doc/ghi.

Trc mat 3 nhom config:
  - pool_url            : URL connect toi pool/SaaS (dung o phase sau)
  - captcha_provider/key: nha giai captcha + API key
  - ram_overflow_percent: % RAM coi la "tran" -> node day, phai giam moi claim tiep
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def default_config_path() -> Path:
    env = os.environ.get("RLX_NODE_CONFIG")
    if env:
        return Path(env)
    return Path.home() / ".roblox-node" / "config.json"


def _default_node_name() -> str:
    return os.uname().nodename if hasattr(os, "uname") else "node"


@dataclass
class NodeConfig:
    # 1. connect toi pool (phase sau)
    pool_url: str = ""
    # 2. captcha
    captcha_provider: str = "yescaptcha"
    captcha_key: str = ""
    # 3. tai nguyen: RAM vuot nguong nay (%) -> node "day", ngung claim toi khi tut xuong
    ram_overflow_percent: int = 85
    # 4. song song: so phien browser toi da chay cung luc (kem RAM gate o tren)
    max_concurrent: int = 10
    # 5. cua so spawn LUC LOGIN = desktop (fullwidth, layout PC); xep luoi khong de
    #    nhau. Toi man /not-approved flow tu thu nho ve mobile.
    win_w: int = 900
    win_h: int = 760
    win_gap: int = 8
    # kich thuoc man hinh de tinh luoi; 0 = tu do
    screen_w: int = 0
    screen_h: int = 0
    # 6. XOAY PROXY: danh sach proxy (moi dong 1 proxy, 4 dinh dang deu duoc:
    #    ip:port:user:pass | user:pass@ip:port | protocol://ip:port:user:pass |
    #    protocol://user:pass@ip:port). Rong = khong dung proxy.
    proxies: str = ""
    # Cu N browser (spawn) thi doi sang proxy tiep theo. Mac dinh 30.
    proxy_rotate_every: int = 30
    # tien ich khac (de san)
    node_name: str = field(default_factory=_default_node_name)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, path: Path | None = None) -> NodeConfig:
        path = path or default_config_path()
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        known = {f for f in cls().to_dict()}
        return cls(**{k: v for k, v in data.items() if k in known})

    def save(self, path: Path | None = None) -> Path:
        path = path or default_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    # --- validate nhe cho form ---
    def normalized(self) -> NodeConfig:
        self.ram_overflow_percent = max(10, min(99, int(self.ram_overflow_percent)))
        self.max_concurrent = max(1, min(200, int(self.max_concurrent)))
        self.win_w = max(200, min(1200, int(self.win_w)))
        self.win_h = max(300, min(1600, int(self.win_h)))
        self.win_gap = max(0, min(80, int(self.win_gap)))
        self.screen_w = max(0, int(self.screen_w))
        self.screen_h = max(0, int(self.screen_h))
        self.pool_url = self.pool_url.strip()
        self.captcha_key = self.captcha_key.strip()
        self.captcha_provider = (self.captcha_provider or "yescaptcha").strip()
        self.proxies = (self.proxies or "").strip()
        self.proxy_rotate_every = max(1, min(1000, int(self.proxy_rotate_every)))
        return self

    def proxy_list(self) -> list[str]:
        """Cac dong proxy hop le (bo trong / comment / dong sai dinh dang)."""
        from app.domain.models import Proxy

        out: list[str] = []
        for raw in (self.proxies or "").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                Proxy.parse(line)   # validate
                out.append(line)
            except (ValueError, Exception):  # noqa: BLE001 - dong sai -> bo qua
                continue
        return out


# danh sach nha captcha cho dropdown - trc mat chi yescaptcha
CAPTCHA_PROVIDERS = ["yescaptcha"]
