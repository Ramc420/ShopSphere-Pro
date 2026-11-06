from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    notification_type: Optional[str] = "SYSTEM"
    severity: Optional[str] = "INFO"
    reference_id: Optional[str] = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    severity: str
    reference_id: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    unread_count: int

