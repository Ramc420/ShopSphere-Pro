from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ReturnRequest(Base):
    """
    Module 36: Return Management
    Customer returns, item quantities, eligibility verification,
    and administrative review/refund status.
    """
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    return_number = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="REQUESTED", index=True, nullable=False)  # REQUESTED, APPROVED, REJECTED, ITEMS_RECEIVED, REFUNDED, CANCELLED
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    order = relationship("Order")
    user = relationship("User")
    items = relationship("ReturnItem", back_populates="return_request", cascade="all, delete-orphan")


class ReturnItem(Base):
    """
    Module 36: Return Line Items
    Tracks specific order item IDs, returned quantities, and item conditions.
    """
    __tablename__ = "return_items"

    id = Column(Integer, primary_key=True, index=True)
    return_request_id = Column(Integer, ForeignKey("return_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    item_condition = Column(String(50), default="UNOPENED", nullable=False)  # UNOPENED, OPEN_BOX, DAMAGED, DEFECTIVE

    return_request = relationship("ReturnRequest", back_populates="items")
    order_item = relationship("OrderItem")


class ExchangeRequest(Base):
    """
    Module 37: Exchange Management
    Product replacement requests, replacement inventory validation,
    and exchange status tracking.
    """
    __tablename__ = "exchange_requests"

    id = Column(Integer, primary_key=True, index=True)
    exchange_number = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_item_id = Column(Integer, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    replacement_variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="REQUESTED", index=True, nullable=False)  # REQUESTED, APPROVED, REJECTED, DISPATCHED, COMPLETED
    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    order = relationship("Order")
    user = relationship("User")
    original_item = relationship("OrderItem")
    replacement_variant = relationship("ProductVariant")

