from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class TicketMessageCreate(BaseModel):
    message: str
    is_internal_note: bool = False


class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_user_id: int
    message: str
    is_internal_note: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupportTicketCreate(BaseModel):
    subject: str
    category: str = "GENERAL"  # ORDER_ISSUE, PAYMENT, RETURN, PRODUCT_INQUIRY, GENERAL
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT
    message: str
    order_id: Optional[int] = None
    product_id: Optional[int] = None


class TicketAssignRequest(BaseModel):
    assigned_to_user_id: int


class TicketStatusUpdate(BaseModel):
    status: str  # OPEN, IN_PROGRESS, WAITING_FOR_CUSTOMER, RESOLVED, CLOSED


class SupportTicketResponse(BaseModel):
    id: int
    ticket_number: str
    user_id: int
    order_id: Optional[int] = None
    product_id: Optional[int] = None
    subject: str
    category: str
    priority: str
    status: str
    assigned_to_user_id: Optional[int] = None
    messages: List[TicketMessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

