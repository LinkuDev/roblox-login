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


@dataclass
class NodeConfig:
    # 1. connect toi pool (phase sau)
    pool_url: str = ""
    # 2. captcha
    captcha_provider: str = "yescaptcha"
    captcha_key: str = ""
    # 3. tai nguyen: RAM vuot nguong nay (%) -> node "day", ngung claim toi khi tut xuong
    ram_overflow_percent: int = 85
    # tien ich khac (de san)
    node_name: str = field(default_factory=lambda: os.uname().nodename if hasattr(os, "uname") else "node")

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
        self.pool_url = self.pool_url.strip()
        self.captcha_key = self.captcha_key.strip()
        self.captcha_provider = (self.captcha_provider or "yescaptcha").strip()
        return self


# danh sach nha captcha cho dropdown - trc mat chi yescaptcha
CAPTCHA_PROVIDERS = ["yescaptcha"]
