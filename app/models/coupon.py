from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    discount_type = Column(String(32), default="PERCENTAGE", nullable=False)  # PERCENTAGE, FIXED_AMOUNT
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_purchase_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    max_discount_amount = Column(Numeric(10, 2), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    usages = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")


class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    discount_applied = Column(Numeric(10, 2), default=0.00, nullable=False)
    used_at = Column(DateTime, default=utc_now, nullable=False)

    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User")

