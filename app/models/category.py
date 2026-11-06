from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    slug = Column(String(150), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    image_url = Column(String(500), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Self-referential relationship for hierarchies
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all"
    )
    parent = relationship("Category", back_populates="children", remote_side=[id])
    products = relationship("Product", back_populates="category")
