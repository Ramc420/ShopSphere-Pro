from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class TaxRate(Base):
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(3), default="USA", index=True, nullable=False)
    state_province = Column(String(64), default="*", index=True, nullable=False)
    postal_code = Column(String(32), nullable=True)
    rate_percentage = Column(Numeric(5, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    category = relationship("Category")
    history = relationship("TaxHistory", back_populates="tax_rate", cascade="all, delete-orphan")


class TaxHistory(Base):
    __tablename__ = "tax_history"

    id = Column(Integer, primary_key=True, index=True)
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.id", ondelete="CASCADE"), nullable=False, index=True)
    old_rate = Column(Numeric(5, 2), nullable=False)
    new_rate = Column(Numeric(5, 2), nullable=False)
    change_reason = Column(String(255), nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    tax_rate = relationship("TaxRate", back_populates="history")
    changed_by = relationship("User")

