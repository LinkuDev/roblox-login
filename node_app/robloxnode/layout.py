"""Chia man hinh thanh luoi o cua so (tiling) cho cac phien browser spawn song song.

Xep trai -> phai, tren -> duoi, khong de nhau. Moi claim acquire() 1 o trong nhat
(index nho nhat con trong) -> tu lap vao cho trong khi 1 phien xong va release().
"""

from __future__ import annotations

import threading


def detect_screen(default: tuple[int, int] = (1920, 1080)) -> tuple[int, int]:
    """Do kich thuoc man hinh (best-effort, cross-platform). Loi -> default."""
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        if w > 0 and h > 0:
            return int(w), int(h)
    except Exception:  # noqa: BLE001 - khong co display/tk -> dung default
        pass
    return default


class SlotAllocator:
    """Cap phat vi tri cua so theo luoi. Thread-safe."""

    def __init__(
        self,
        screen: tuple[int, int],
        window: tuple[int, int],
        gap: int = 6,
        margin_top: int = 0,
    ) -> None:
        self.sw, self.sh = screen
        self.ww, self.wh = window
        self.gap = gap
        self.margin_top = margin_top
        self.cols = max(1, self.sw // (self.ww + gap))
        self.rows = max(1, (self.sh - margin_top) // (self.wh + gap))
        self.per_screen = self.cols * self.rows
        self._used: set[int] = set()
        self._lock = threading.Lock()

    def acquire(self) -> int:
        """Index o trong nho nhat (lap cho trong)."""
        with self._lock:
            i = 0
            while i in self._used:
                i += 1
            self._used.add(i)
            return i

    def release(self, idx: int) -> None:
        with self._lock:
            self._used.discard(idx)

    def position(self, idx: int) -> tuple[int, int]:
        """(x, y) cua o idx. Vuot man hinh -> cascade lech nhe cho khoi trung."""
        local = idx % self.per_screen
        layer = idx // self.per_screen
        col = local % self.cols
        row = local // self.cols
        off = layer * 24
        x = col * (self.ww + self.gap) + off
        y = self.margin_top + row * (self.wh + self.gap) + off
        return x, y

    def placement(self, idx: int) -> dict:
        """Goi cho run_service: vi tri + kich thuoc cua so cho phien nay."""
        x, y = self.position(idx)
        return {"window_position": (x, y), "window_size": (self.ww, self.wh)}
