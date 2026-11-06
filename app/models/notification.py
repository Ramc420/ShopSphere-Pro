from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="SYSTEM", index=True)  # ORDER_UPDATE, PAYMENT_STATUS, REFUND_STATUS, INVENTORY_EXCEPTION, SYSTEM
    severity = Column(String(20), default="INFO")  # INFO, SUCCESS, WARNING, CRITICAL
    reference_id = Column(String(100), nullable=True, index=True)
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", foreign_keys=[user_id])

