from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class OrderItemIn(BaseModel):
    id_product: str = Field(..., alias="idProduct")

    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("quantity must be greater than 0")
        return v

    model_config = {"populate_by_name": True}


class OrderIn(BaseModel):
    items: List[OrderItemIn]

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("items must not be empty")
        return v


class ProductOut(BaseModel):
    id: str


class OrderItemOut(BaseModel):
    id: str
    product: ProductOut
    quantity: int
    total: float


class OrderDetailOut(BaseModel):
    id: str
    date: datetime
    currency: str
    items: List[OrderItemOut]
    total: float


class OrderSummaryOut(BaseModel):
    id: str
    date: datetime
    total: float
