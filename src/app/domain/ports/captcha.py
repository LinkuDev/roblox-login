"""Port giai captcha.

Doi 2captcha -> capsolver/anticaptcha/self-host: chi can them 1 class implement
interface nay va dang ky vao registry. Khong tang nao khac phai sua.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.enums import CaptchaType
from app.domain.models import CaptchaSolution, CaptchaTask


class CaptchaSolver(ABC):
    name: str = "base"
    supported: frozenset[CaptchaType] = frozenset()

    @abstractmethod
    def solve(self, task: CaptchaTask) -> CaptchaSolution:
        """Giai captcha (blocking). Raise CaptchaTimeout/CaptchaUnsolvable khi that bai."""

    @abstractmethod
    def balance(self) -> float:
        """So du tai khoan (USD)."""

    def supports(self, captcha_type: CaptchaType) -> bool:
        return captcha_type in self.supported

    def report_bad(self, solution: CaptchaSolution) -> None:
        """Bao token sai de duoc hoan tien. Optional."""

    def report_good(self, solution: CaptchaSolution) -> None:
        """Optional."""

    def close(self) -> None:
        """Dong ket noi / http client."""
