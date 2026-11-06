from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Attribute(Base):
    __tablename__ = "attributes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(100), unique=True, index=True, nullable=False)
    data_type = Column(String(20), default="TEXT", nullable=False)  # TEXT, NUMBER, SELECT, BOOLEAN
    is_required = Column(Boolean, default=False, nullable=False)
    is_filterable = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    options = relationship("AttributeOption", back_populates="attribute", cascade="all, delete-orphan")
    category_links = relationship("CategoryAttribute", back_populates="attribute", cascade="all, delete-orphan")
    product_values = relationship("ProductAttributeValue", back_populates="attribute", cascade="all, delete-orphan")


class AttributeOption(Base):
    __tablename__ = "attribute_options"

    id = Column(Integer, primary_key=True, index=True)
    attribute_id = Column(Integer, ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(String(150), nullable=False)
    display_order = Column(Integer, default=0, nullable=False)

    attribute = relationship("Attribute", back_populates="options")


class CategoryAttribute(Base):
    __tablename__ = "category_attributes"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_id = Column(Integer, ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    is_required = Column(Boolean, default=False, nullable=False)

    attribute = relationship("Attribute", back_populates="category_links")
    category = relationship("Category")

    __table_args__ = (
        UniqueConstraint("category_id", "attribute_id", name="uq_category_attribute"),
    )


class ProductAttributeValue(Base):
    __tablename__ = "product_attribute_values"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_id = Column(Integer, ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    attribute = relationship("Attribute", back_populates="product_values")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("product_id", "attribute_id", name="uq_product_attribute"),
    )

