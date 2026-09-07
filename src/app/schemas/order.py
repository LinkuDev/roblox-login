from __future__ import annotations

from pydantic import BaseModel, Field


class AccountInput(BaseModel):
    username: str
    password: str
    totp_secret: str | None = None
    email: str | None = None


class CreateOrderRequest(BaseModel):
    service_id: str = Field(examples=["roblox.login"])
    inputs: list[AccountInput]
    note: str = ""


class OrderItemResponse(BaseModel):
    id: str
    status: str


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


class ServiceInfo(BaseModel):
    id: str
    name: str
    category: str
    price_points: int
    description: str
    input_fields: list[str]
