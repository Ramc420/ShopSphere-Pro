from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ProductPrice(Base):
    __tablename__ = "product_prices"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    base_price = Column(Numeric(12, 2), nullable=False)
    sale_price = Column(Numeric(12, 2), nullable=True)
    sale_start_date = Column(DateTime, nullable=True)
    sale_end_date = Column(DateTime, nullable=True)
    
    currency = Column(String(10), default="USD", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    @property
    def sale_start_at(self):
        return self.sale_start_date

    @sale_start_at.setter
    def sale_start_at(self, value):
        self.sale_start_date = value

    @property
    def sale_end_at(self):
        return self.sale_end_date

    @sale_end_at.setter
    def sale_end_at(self, value):
        self.sale_end_date = value

    product = relationship("Product")
    variant = relationship("ProductVariant")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    old_base_price = Column(Numeric(12, 2), nullable=True)
    new_base_price = Column(Numeric(12, 2), nullable=False)
    old_sale_price = Column(Numeric(12, 2), nullable=True)
    new_sale_price = Column(Numeric(12, 2), nullable=True)
    
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("Product")
    variant = relationship("ProductVariant")
    changed_by = relationship("User")

