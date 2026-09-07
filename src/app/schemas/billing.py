from __future__ import annotations

from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    balance: int


class TopupRequest(BaseModel):
    user_id: str
    amount: int = Field(gt=0)
    note: str = ""


class TransactionResponse(BaseModel):
    type: str
    amount: int
    balance_after: int
    note: str

    class Config:
        from_attributes = True
