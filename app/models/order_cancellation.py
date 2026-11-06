from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class OrderCancellation(Base):
    """
    Module 28: Order Cancellation
    Stores customer cancellation requests, reasons, approval outcomes,
    and records whether reserved stock and payment refunds were triggered.
    """
    __tablename__ = "order_cancellations"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="REQUESTED", nullable=False)  # REQUESTED, APPROVED, REJECTED, COMPLETED
    refund_initiated = Column(Boolean, default=False, nullable=False)
    inventory_released = Column(Boolean, default=True, nullable=False)
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    order = relationship("Order")
    user = relationship("User")

