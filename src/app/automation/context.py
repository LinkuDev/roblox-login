"""Context truyen qua tat ca step - cho phep step chia se du lieu ma khong coupling."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.domain.models import Credential, Proxy, SessionArtifact
from app.domain.ports import ArtifactStorage, BrowserSession, CaptchaSolver


@dataclass
class ExecutionContext:
    credential: Credential
    browser: BrowserSession
    solver: CaptchaSolver
    settings: Settings = field(default_factory=get_settings)
    proxy: Proxy | None = None
    storage: ArtifactStorage | None = None
    job_id: str = "local"
    options: dict[str, Any] = field(default_factory=dict)

    # --- state chia se giua cac step ---
    bag: dict[str, Any] = field(default_factory=dict)
    session: SessionArtifact = field(default_factory=SessionArtifact)
    artifacts: list[str] = field(default_factory=list)
    cost: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.log = get_logger("flow", job_id=self.job_id, user=self.credential.username)

    # --- helpers -----------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self.bag.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.bag[key] = value

    def option(self, key: str, default: Any = None) -> Any:
        return self.options.get(key, default)

    def add_cost(self, kind: str, amount: float | None) -> None:
        if amount:
            self.cost[kind] = round(self.cost.get(kind, 0.0) + amount, 6)

    def snapshot(self, label: str) -> str | None:
        """Chup man hinh de debug khi step loi."""
        try:
            out_dir = Path(self.settings.root_dir) / "data" / "screenshots" / self.job_id
            out_dir.mkdir(parents=True, exist_ok=True)
            path = str(out_dir / f"{label}.png")
            saved = self.browser.screenshot(path)
            if saved:
                key = saved
                if self.storage:
                    key = self.storage.save_file(f"{self.job_id}/{label}.png", saved)
                self.artifacts.append(key)
                return key
        except Exception as exc:  # screenshot loi khong duoc lam hong flow
            self.log.warning("snapshot_failed", label=label, error=str(exc))
        return None
