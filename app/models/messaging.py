from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class NotificationProviderConfig(Base):
    __tablename__ = "notification_provider_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider_type = Column(String(20), nullable=False, index=True)  # EMAIL, SMS
    provider_name = Column(String(100), nullable=False)            # SendGrid, Twilio, AWS_SES, Mock
    sender_address = Column(String(255), nullable=False)           # no-reply@shopsphere.com / +18005550199
    api_key_masked = Column(String(100), nullable=True)            # sk_live_****
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String(20), nullable=False, index=True)       # EMAIL, SMS
    recipient = Column(String(255), nullable=False, index=True)
    template_type = Column(String(50), nullable=False, index=True) # VERIFICATION, ORDER_CONFIRMATION, SHIPMENT_UPDATE, DELIVERY_UPDATE, CUSTOM
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String(30), default="SENT", index=True)        # SENT, FAILED, PENDING, DELIVERED
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

