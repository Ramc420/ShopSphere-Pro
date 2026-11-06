from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.order import OrderStatusHistoryResponse


class OrderStatusTransitionRequest(BaseModel):
    to_status: str  # PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED
    notes: Optional[str] = None


class PermittedTransitionsResponse(BaseModel):
    current_status: str
    permitted_next_statuses: List[str]
    order_id: int

