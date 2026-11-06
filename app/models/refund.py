from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Refund(Base):
    """
    Module 31: Refund Management
    Tracks full and partial refund requests, refundable amount validations,
    gateway processing references, and audit history.
    """
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    refund_number = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="REQUESTED", nullable=False)  # REQUESTED, PROCESSING, COMPLETED, REJECTED
    gateway_refund_id = Column(String(100), nullable=True)
    processed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    order = relationship("Order")
    payment = relationship("Payment")
    user = relationship("User", foreign_keys=[user_id])
    processor = relationship("User", foreign_keys=[processed_by_user_id])

