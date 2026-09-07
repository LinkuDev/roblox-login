from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ArtifactStorage(ABC):
    """Luu screenshot / cookie dump / log cua tung job. Local now, S3 sau."""

    name: str = "base"

    @abstractmethod
    def save_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str: ...

    @abstractmethod
    def save_file(self, key: str, path: str | Path) -> str: ...

    @abstractmethod
    def url_for(self, key: str) -> str: ...
