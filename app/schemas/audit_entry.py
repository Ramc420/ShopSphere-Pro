from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogEntryCreate(BaseModel):
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    reason: Optional[str] = None


class AuditLogEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    ip_address: Optional[str] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    reason: Optional[str] = None
    is_immutable: bool
    created_at: datetime

