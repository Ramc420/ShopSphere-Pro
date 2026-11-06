from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ReturnItemCreate(BaseModel):
    order_item_id: int
    quantity: int = 1
    item_condition: str = "UNOPENED"  # UNOPENED, OPEN_BOX, DAMAGED, DEFECTIVE


class ReturnItemResponse(BaseModel):
    id: int
    return_request_id: int
    order_item_id: int
    quantity: int
    item_condition: str

    model_config = ConfigDict(from_attributes=True)


class ReturnRequestCreate(BaseModel):
    order_id: int
    reason: str
    items: List[ReturnItemCreate]


class ReturnReview(BaseModel):
    status: str  # APPROVED, REJECTED, ITEMS_RECEIVED, REFUNDED
    admin_notes: Optional[str] = None


class ReturnRequestResponse(BaseModel):
    id: int
    return_number: str
    order_id: int
    user_id: int
    reason: str
    status: str
    admin_notes: Optional[str] = None
    items: List[ReturnItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExchangeRequestCreate(BaseModel):
    order_id: int
    original_item_id: int
    replacement_variant_id: int
    quantity: int = 1
    reason: str


class ExchangeReview(BaseModel):
    status: str  # APPROVED, REJECTED, DISPATCHED, COMPLETED
    admin_notes: Optional[str] = None


class ExchangeRequestResponse(BaseModel):
    id: int
    exchange_number: str
    order_id: int
    user_id: int
    original_item_id: int
    replacement_variant_id: int
    quantity: int
    reason: str
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

