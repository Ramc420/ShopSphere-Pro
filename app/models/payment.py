from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Payment(Base):
    """
    Module 29: Payment Management
    Tracks payment intent/session, gateway transaction references,
    idempotency keys, and transaction status.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_method = Column(String(50), default="MOCK_GATEWAY", nullable=False)  # CREDIT_CARD, PAYPAL, STRIPE, COD, MOCK_GATEWAY
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(String(50), default="PENDING", index=True, nullable=False)  # PENDING, SUCCESSFUL, FAILED, CANCELLED
    gateway_provider = Column(String(50), default="SANDBOX_GATEWAY", nullable=False)
    transaction_reference = Column(String(100), unique=True, index=True, nullable=False)
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    order = relationship("Order")
    user = relationship("User")
    transactions = relationship("PaymentTransaction", back_populates="payment", cascade="all, delete-orphan")


class PaymentTransaction(Base):
    """
    Module 30: Payment Transaction History
    Immutable audit ledger of payment attempts, webhooks, callbacks,
    and gateway responses.
    """
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # INITIATE, AUTHORIZE, CAPTURE, FAIL, WEBHOOK_VERIFY, REFUND
    status = Column(String(50), nullable=False)  # SUCCESS, FAILURE, PENDING
    gateway_reference = Column(String(100), nullable=True, index=True)
    response_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    payment = relationship("Payment", back_populates="transactions")
    order = relationship("Order")

