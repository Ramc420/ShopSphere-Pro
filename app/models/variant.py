from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(150), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    compare_at_price = Column(Numeric(12, 2), nullable=True)
    cost_price = Column(Numeric(12, 2), nullable=True)
    
    # Store variations e.g. {"size": "XL", "color": "Black", "material": "Cotton"}
    attributes_json = Column(Text, nullable=True)
    
    stock_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=5, nullable=False)
    availability_status = Column(String(20), default="IN_STOCK", nullable=False, index=True)  # IN_STOCK, LOW_STOCK, OUT_OF_STOCK
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, INACTIVE, DISCONTINUED
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product", back_populates="variants")
    media = relationship("ProductMedia", back_populates="variant")

