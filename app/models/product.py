from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    short_description = Column(Text, nullable=True)
    base_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=True)
    compare_at_price = Column(Numeric(12, 2), nullable=True)
    base_sku = Column(String(100), unique=True, index=True, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, INACTIVE, DRAFT, ARCHIVED
    is_featured = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    media = relationship("ProductMedia", back_populates="product", cascade="all, delete-orphan")

