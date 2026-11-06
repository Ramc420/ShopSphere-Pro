from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class PaymentInitiate(BaseModel):
    order_id: int
    payment_method: str = "MOCK_GATEWAY"  # CREDIT_CARD, PAYPAL, STRIPE, COD, MOCK_GATEWAY
    idempotency_key: Optional[str] = None


class PaymentProcessSandbox(BaseModel):
    action: str = "CAPTURE"  # CAPTURE, FAIL, CANCEL
    gateway_reference: Optional[str] = None


class PaymentWebhook(BaseModel):
    event_type: str
    transaction_reference: str
    status: str
    provider_payload: Optional[Dict[str, Any]] = None


class PaymentTransactionResponse(BaseModel):
    id: int
    payment_id: int
    order_id: int
    action: str
    status: str
    gateway_reference: Optional[str] = None
    response_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    payment_method: str
    amount: float
    currency: str
    status: str
    gateway_provider: str
    transaction_reference: str
    idempotency_key: Optional[str] = None
    transactions: List[PaymentTransactionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

