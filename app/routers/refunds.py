import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.payment import Payment, PaymentTransaction
from app.models.refund import Refund
from app.schemas.refund import RefundCreate, RefundResponse
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/refunds", tags=["Module 31: Refund Management"])


@router.post("/", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def create_refund_request(
    payload: RefundCreate,
    current_user: User = Depends(require_permissions(Permission.REFUNDS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 31: Create full or partial refund requests.
    Validates that requested refund does not exceed paid amount minus prior refunds.
    Processes refund through sandbox payment gateway and logs transaction attempt.
    """
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if order.payment_status not in ["PAID", "PARTIALLY_REFUNDED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be refunded. Current payment status is '{order.payment_status}'."
        )

    # Calculate previously refunded amount
    past_refunds = db.query(Refund).filter(
        Refund.order_id == order.id,
        Refund.status == "COMPLETED"
    ).all()
    total_refunded_so_far = sum(r.amount for r in past_refunds)
    remaining_refundable = Decimal(str(order.total_amount)) - Decimal(str(total_refunded_so_far))

    req_amount = Decimal(str(payload.amount))
    if req_amount <= Decimal("0.00"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund amount must be greater than zero")

    if req_amount > remaining_refundable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requested refund (${float(req_amount):.2f}) exceeds remaining refundable balance (${float(remaining_refundable):.2f})"
        )

    # Find associated payment
    payment = None
    if payload.payment_id:
        payment = db.query(Payment).filter(Payment.id == payload.payment_id).first()
    else:
        payment = db.query(Payment).filter(
            Payment.order_id == order.id,
            Payment.status == "SUCCESSFUL"
        ).first()

    refund_ref = f"REF-{uuid.uuid4().hex[:8].upper()}"
    gw_ref = f"GW-REFUND-{uuid.uuid4().hex[:6].upper()}"

    refund = Refund(
        refund_number=refund_ref,
        order_id=order.id,
        payment_id=payment.id if payment else None,
        user_id=order.user_id,
        amount=req_amount,
        reason=payload.reason,
        status="COMPLETED",
        gateway_refund_id=gw_ref,
        processed_by_user_id=current_user.id,
        admin_notes=payload.admin_notes
    )
    db.add(refund)

    # Update order payment status
    if (total_refunded_so_far + req_amount) >= Decimal(str(order.total_amount)):
        order.payment_status = "REFUNDED"
    else:
        order.payment_status = "PARTIALLY_REFUNDED"

    # Log payment transaction if payment exists
    if payment:
        tx = PaymentTransaction(
            payment_id=payment.id,
            order_id=order.id,
            action="REFUND",
            status="SUCCESS",
            gateway_reference=gw_ref,
            response_payload={
                "refund_amount": float(req_amount),
                "remaining_balance": float(remaining_refundable - req_amount),
                "gateway_status": "PROCESSED"
            }
        )
        db.add(tx)

    db.commit()
    db.refresh(refund)
    return refund


@router.get("/", response_model=List[RefundResponse])
def list_refunds(
    order_id: Optional[int] = None,
    current_user: User = Depends(require_permissions(Permission.REFUNDS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve list of refunds with optional order filtering.
    """
    query = db.query(Refund)
    if order_id:
        query = query.filter(Refund.order_id == order_id)

    if current_user.role == "CUSTOMER":
        query = query.filter(Refund.user_id == current_user.id)

    refunds = query.order_by(Refund.created_at.desc()).all()
    return refunds


@router.get("/{refund_id}", response_model=RefundResponse)
def get_refund_details(
    refund_id: int,
    current_user: User = Depends(require_permissions(Permission.REFUNDS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve refund details by ID.
    """
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund record not found")

    if current_user.role == "CUSTOMER" and refund.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return refund


@router.get("/order/{order_id}", response_model=List[RefundResponse])
def get_refunds_for_order(
    order_id: int,
    current_user: User = Depends(require_permissions(Permission.REFUNDS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve all refund history for a specific order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    refunds = db.query(Refund).filter(Refund.order_id == order_id).all()
    return refunds

