from __future__ import annotations

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    service_id: str = Field(examples=["roblox.login"])
    accounts: str = Field(
        description="Payload user:pass, moi dong 1 account",
        examples=["user1:pass1\nuser2:pass2"],
    )
    note: str = ""


class LineErrorResponse(BaseModel):
    line: int
    raw: str
    error: str


class ValidateOrderResponse(BaseModel):
    """Ket qua dry-run cho form: bao truoc so diem se tru + cac dong loi."""

    service_id: str
    valid_count: int
    invalid_count: int
    unit_price: int
    total_price: int
    errors: list[LineErrorResponse]


class OrderResponse(BaseModel):
    id: str
    service_id: str
    status: str
    quantity: int
    unit_price: int
    total_price: int
    completed_count: int
    failed_count: int

    class Config:
        from_attributes = True


class RecordDetail(BaseModel):
    """1 record trong don (kem ket qua/cookie cho chu don)."""

    id: str
    order_id: str
    username: str
    status: str
    attempt: int
    error_code: str
    reason: str
    cookies: str
    duration: float
    created_at: str


class ServiceInfo(BaseModel):
    id: str
    name: str
    category: str
    price_points: int
    description: str
    input_fields: list[str]
