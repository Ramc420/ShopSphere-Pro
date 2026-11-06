from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    website_url = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)  # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    products = relationship("Product", back_populates="brand")

