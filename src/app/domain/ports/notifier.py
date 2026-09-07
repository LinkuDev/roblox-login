from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Notifier(ABC):
    """Bao ket qua job ra ngoai: webhook / telegram / email."""

    name: str = "base"

    @abstractmethod
    def send(self, event: str, payload: dict[str, Any]) -> None: ...
