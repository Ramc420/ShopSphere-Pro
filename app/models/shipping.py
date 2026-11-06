from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ShippingMethod(Base):
    __tablename__ = "shipping_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    base_charge = Column(Numeric(10, 2), default=0.00, nullable=False)
    free_shipping_threshold = Column(Numeric(10, 2), nullable=True)
    estimated_days_min = Column(Integer, default=3, nullable=False)
    estimated_days_max = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    rules = relationship("ShippingRule", back_populates="shipping_method", cascade="all, delete-orphan")


class ShippingRule(Base):
    __tablename__ = "shipping_rules"

    id = Column(Integer, primary_key=True, index=True)
    shipping_method_id = Column(Integer, ForeignKey("shipping_methods.id", ondelete="CASCADE"), nullable=False, index=True)
    country = Column(String(3), default="USA", nullable=False)
    state_province = Column(String(64), nullable=True)
    extra_surcharge = Column(Numeric(10, 2), default=0.00, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    shipping_method = relationship("ShippingMethod", back_populates="rules")

