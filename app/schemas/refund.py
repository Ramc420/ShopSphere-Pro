from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RefundCreate(BaseModel):
    order_id: int
    payment_id: Optional[int] = None
    amount: float
    reason: str
    admin_notes: Optional[str] = None


class RefundResponse(BaseModel):
    id: int
    refund_number: str
    order_id: int
    payment_id: Optional[int] = None
    user_id: int
    amount: float
    reason: str
    status: str
    gateway_refund_id: Optional[str] = None
    processed_by_user_id: Optional[int] = None
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

