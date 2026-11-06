import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.payment import Payment, PaymentTransaction
from app.schemas.payment import (
    PaymentInitiate, PaymentProcessSandbox, PaymentWebhook,
    PaymentResponse, PaymentTransactionResponse
)
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/payments", tags=["Module 29 & 30: Payment Management & Transaction History"])


@router.post("/initiate", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def initiate_payment(
    payload: PaymentInitiate,
    current_user: User = Depends(require_permissions(Permission.PAYMENTS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 29: Create payment request in sandbox mode.
    Validates order status and prevents duplicate payment processing via idempotency keys.
    """
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot pay for another user's order")

    if order.payment_status == "PAID":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order has already been paid")

    # Idempotency check
    if payload.idempotency_key:
        existing_pay = db.query(Payment).filter(Payment.idempotency_key == payload.idempotency_key).first()
        if existing_pay:
            return existing_pay

    ref = f"PAY-{uuid.uuid4().hex[:10].upper()}"
    payment = Payment(
        order_id=order.id,
        user_id=current_user.id,
        payment_method=payload.payment_method,
        amount=order.total_amount,
        currency="USD",
        status="PENDING",
        gateway_provider="SANDBOX_GATEWAY",
        transaction_reference=ref,
        idempotency_key=payload.idempotency_key
    )
    db.add(payment)
    db.flush()

    # Log initial transaction attempt
    tx = PaymentTransaction(
        payment_id=payment.id,
        order_id=order.id,
        action="INITIATE",
        status="PENDING",
        gateway_reference=ref,
        response_payload={"message": "Payment session initialized in Sandbox"}
    )
    db.add(tx)
    db.commit()
    db.refresh(payment)

    return payment


@router.post("/{payment_id}/process-sandbox", response_model=PaymentResponse)
def process_sandbox_payment(
    payment_id: int,
    payload: PaymentProcessSandbox,
    current_user: User = Depends(require_permissions(Permission.PAYMENTS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 29: Process / capture payment in sandbox gateway mode.
    Simulates gateway authorization, updates payment and order status, and logs transaction attempt.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    if current_user.role == "CUSTOMER" and payment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if payment.status == "SUCCESSFUL":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment is already completed")

    order = db.query(Order).filter(Order.id == payment.order_id).first()

    action = payload.action.upper()
    if action == "CAPTURE":
        payment.status = "SUCCESSFUL"
        if order:
            order.payment_status = "PAID"

        tx = PaymentTransaction(
            payment_id=payment.id,
            order_id=payment.order_id,
            action="CAPTURE",
            status="SUCCESS",
            gateway_reference=payload.gateway_reference or f"AUTH-{uuid.uuid4().hex[:8].upper()}",
            response_payload={"gateway_code": "200", "status": "APPROVED", "avs_check": "MATCH"}
        )
        db.add(tx)

    elif action == "FAIL":
        payment.status = "FAILED"
        tx = PaymentTransaction(
            payment_id=payment.id,
            order_id=payment.order_id,
            action="CAPTURE",
            status="FAILURE",
            gateway_reference=payload.gateway_reference or f"ERR-{uuid.uuid4().hex[:8].upper()}",
            error_message="Card declined: Insufficient funds (Simulated Sandbox Rejection)",
            response_payload={"gateway_code": "402", "status": "DECLINED"}
        )
        db.add(tx)

    db.commit()
    db.refresh(payment)
    return payment


@router.post("/webhook", status_code=status.HTTP_200_OK)
def payment_gateway_webhook(
    payload: PaymentWebhook,
    db: Session = Depends(get_db)
):
    """
    Module 29: Verify gateway callbacks or webhooks from external providers.
    Prevents duplicate payment processing and updates order status.
    """
    payment = db.query(Payment).filter(Payment.transaction_reference == payload.transaction_reference).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction reference not recognized")

    if payment.status == "SUCCESSFUL" and payload.status.upper() == "SUCCESSFUL":
        return {"status": "ALREADY_PROCESSED", "detail": "Payment was already confirmed"}

    new_status = payload.status.upper()
    payment.status = new_status

    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if order and new_status == "SUCCESSFUL":
        order.payment_status = "PAID"

    tx = PaymentTransaction(
        payment_id=payment.id,
        order_id=payment.order_id,
        action="WEBHOOK_VERIFY",
        status="SUCCESS" if new_status == "SUCCESSFUL" else "FAILURE",
        gateway_reference=payload.transaction_reference,
        response_payload=payload.provider_payload or {"webhook_event": payload.event_type}
    )
    db.add(tx)
    db.commit()

    return {"status": "PROCESSED", "payment_status": payment.status}


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_details(
    payment_id: int,
    current_user: User = Depends(require_permissions(Permission.PAYMENTS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve payment session status and details.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment record not found")

    if current_user.role == "CUSTOMER" and payment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return payment


@router.get("/order/{order_id}", response_model=List[PaymentResponse])
def get_payments_for_order(
    order_id: int,
    current_user: User = Depends(require_permissions(Permission.PAYMENTS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve all payment records associated with a given order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    payments = db.query(Payment).filter(Payment.order_id == order_id).all()
    return payments


@router.get("/transactions/order/{order_id}", response_model=List[PaymentTransactionResponse])
def get_order_payment_transactions(
    order_id: int,
    current_user: User = Depends(require_permissions(Permission.PAYMENTS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Module 30: Retrieve payment transaction history for an order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    transactions = db.query(PaymentTransaction).filter(PaymentTransaction.order_id == order_id).order_by(PaymentTransaction.created_at.asc()).all()
    return transactions


@router.get("/transactions/", response_model=List[PaymentTransactionResponse])
def list_all_payment_transactions(
    current_user: User = Depends(require_permissions(Permission.AUDIT_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Module 30: Maintain and retrieve comprehensive payment transaction audit records (Admin view).
    """
    transactions = db.query(PaymentTransaction).order_by(PaymentTransaction.created_at.desc()).limit(100).all()
    return transactions

