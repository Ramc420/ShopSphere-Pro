from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    phone_number = Column(String(32), nullable=False)
    address_type = Column(String(20), default="SHIPPING", nullable=False)  # SHIPPING, BILLING, BOTH
    street_line1 = Column(String(255), nullable=False)
    street_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), default="United States", nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    is_default_billing = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="addresses")
    shipping_orders = relationship("Order", foreign_keys="Order.shipping_address_id", back_populates="shipping_address")
    billing_orders = relationship("Order", foreign_keys="Order.billing_address_id", back_populates="billing_address")

