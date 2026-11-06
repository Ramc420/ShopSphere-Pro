from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class SupportTicket(Base):
    """
    Module 40: Customer Support Tickets
    Multi-channel support tickets associated with orders or products,
    agent assignment, priorities, and status workflow.
    """
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    subject = Column(String(200), nullable=False)
    category = Column(String(50), default="GENERAL", nullable=False)  # ORDER_ISSUE, PAYMENT, RETURN, PRODUCT_INQUIRY, GENERAL
    priority = Column(String(50), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    status = Column(String(50), default="OPEN", index=True, nullable=False)  # OPEN, IN_PROGRESS, WAITING_FOR_CUSTOMER, RESOLVED, CLOSED
    assigned_to_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    assigned_agent = relationship("User", foreign_keys=[assigned_to_user_id])
    order = relationship("Order")
    product = relationship("Product")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class TicketMessage(Base):
    """
    Module 40: Support Ticket Messages & Conversation Thread
    Conversation history, internal staff notes, and resolution comments.
    """
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_internal_note = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User")

