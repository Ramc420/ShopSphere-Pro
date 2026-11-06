from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    secondary_email = Column(String(255), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(30), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    marketing_opt_in = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Deactivation request flow (Module 4)
    deactivation_requested = Column(Boolean, default=False, nullable=False)
    deactivation_reason = Column(Text, nullable=True)
    deactivation_requested_at = Column(DateTime, nullable=True)
    deactivation_status = Column(String(50), default="NONE", nullable=False)  # NONE, PENDING, APPROVED, REJECTED, CANCELLED
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="profile")

