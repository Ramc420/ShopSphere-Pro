from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProviderConfigCreate(BaseModel):
    provider_type: str  # EMAIL, SMS
    provider_name: str  # SendGrid, Twilio, AWS_SES, Mock
    sender_address: str
    api_key_masked: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class ProviderConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_type: str
    provider_name: str
    sender_address: str
    api_key_masked: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class SendMessageRequest(BaseModel):
    channel: str  # EMAIL, SMS
    recipient: str
    template_type: str  # VERIFICATION, ORDER_CONFIRMATION, SHIPMENT_UPDATE, DELIVERY_UPDATE, CUSTOM
    subject: Optional[str] = None
    body: str


class MessageLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel: str
    recipient: str
    template_type: str
    subject: Optional[str] = None
    body: str
    status: str
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    last_retry_at: Optional[datetime] = None
    created_at: datetime

