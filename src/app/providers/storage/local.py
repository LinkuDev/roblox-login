from __future__ import annotations

import shutil
from pathlib import Path

from app.core.config import get_settings
from app.domain.ports import ArtifactStorage


class LocalStorage(ArtifactStorage):
    """Luu artifact vao data/artifacts. Doi sang S3 = viet 1 class tuong tu."""

    name = "local"

    def __init__(self, root: Path | None = None):
        self.root = Path(root or get_settings().root_dir / "data" / "artifacts")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def save_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._path(key)
        path.write_bytes(data)
        return key

    def save_file(self, key: str, path: str | Path) -> str:
        dest = self._path(key)
        if Path(path).resolve() != dest.resolve():
            shutil.copy2(path, dest)
        return key

    def url_for(self, key: str) -> str:
        return f"/artifacts/{key}"
