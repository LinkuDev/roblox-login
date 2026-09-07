"""Registry generic: dang ky implementation theo ten -> doi provider khong sua code goi."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from app.core.errors import AppError

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self, kind: str):
        self.kind = kind
        self._items: dict[str, type[T]] = {}

    def register(self, name: str) -> Callable[[type[T]], type[T]]:
        def deco(cls: type[T]) -> type[T]:
            key = name.lower()
            if key in self._items:
                raise AppError(f"{self.kind} '{key}' da duoc dang ky")
            self._items[key] = cls
            return cls

        return deco

    def get(self, name: str) -> type[T]:
        key = (name or "").lower()
        if key not in self._items:
            raise AppError(
                f"khong tim thay {self.kind} '{name}'. Co san: {sorted(self._items)}"
            )
        return self._items[key]

    def names(self) -> list[str]:
        return sorted(self._items)

    def __contains__(self, name: str) -> bool:
        return (name or "").lower() in self._items
