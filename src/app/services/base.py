"""Service = 1 san pham ban cho khach (vd: roblox.login, roblox.signup...).

Moi service:
  - khai bao ServiceSpec: id, gia diem, input schema.
  - build 1 Flow gom cac Step.
  - tra RunResult.
Them service moi = tao class ke thua Service + dang ky. Khong dung vao tang khac.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.automation.context import ExecutionContext
from app.automation.flow import Flow
from app.automation.result import RunResult
from app.domain.models import Credential


@dataclass(slots=True, frozen=True)
class ServiceSpec:
    id: str                      # vd "roblox.login"
    name: str                    # ten hien thi
    category: str                # vd "roblox"
    price_points: int            # gia tru moi lan chay thanh cong
    description: str = ""
    input_fields: tuple[str, ...] = ("username", "password")
    version: str = "1.0"
    tags: tuple[str, ...] = ()


class Service(ABC):
    spec: ServiceSpec

    @abstractmethod
    def build_flow(self, ctx: ExecutionContext) -> Flow:
        """Rap cac step thanh flow. Co the tuy bien theo ctx.options."""

    def validate_input(self, credential: Credential, options: dict[str, Any]) -> None:
        """Kiem tra dau vao truoc khi chay. Raise ValueError neu thieu."""
        if not credential.username or not credential.password:
            raise ValueError("thieu username hoac password")

    def run(self, ctx: ExecutionContext) -> RunResult:
        self.validate_input(ctx.credential, ctx.options)
        flow = self.build_flow(ctx)
        return flow.run(ctx)
