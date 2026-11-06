from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    promotion_type = Column(String(50), default="PERCENTAGE_DISCOUNT", nullable=False)  # PERCENTAGE_DISCOUNT, FIXED_DISCOUNT, CATEGORY_DISCOUNT
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_order_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    target_category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    target_product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    target_category = relationship("Category")
    target_product = relationship("Product")
    history = relationship("PromotionHistory", back_populates="promotion", cascade="all, delete-orphan")


class PromotionHistory(Base):
    __tablename__ = "promotion_history"

    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    discount_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    applied_at = Column(DateTime, default=utc_now, nullable=False)

    promotion = relationship("Promotion", back_populates="history")
    user = relationship("User")

