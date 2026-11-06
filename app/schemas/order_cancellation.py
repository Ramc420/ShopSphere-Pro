from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OrderCancellationCreate(BaseModel):
    reason: str
    admin_notes: Optional[str] = None


class OrderCancellationResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    reason: str
    status: str
    refund_initiated: bool
    inventory_released: bool
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

