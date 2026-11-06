import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Date, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.permissions import UserRole, UserStatus


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(32), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), default=UserRole.CUSTOMER.value, index=True, nullable=False)
    status = Column(String(50), default=UserStatus.ACTIVE.value, index=True, nullable=False)
    
    # Registration & Verification (Module 3)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_expires_at = Column(DateTime, nullable=True)
    registration_status = Column(String(50), default="PENDING_VERIFICATION", nullable=False)
    
    # Employee details
    department = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    profile = relationship("CustomerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", foreign_keys="UserActivityLog.user_id", back_populates="user")
    performed_logs = relationship("UserActivityLog", foreign_keys="UserActivityLog.actor_id", back_populates="actor")
    profile_history = relationship("ProfileChangeHistory", foreign_keys="ProfileChangeHistory.user_id", back_populates="user")
    orders = relationship("Order", back_populates="user")

