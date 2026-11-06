from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderStatusHistory
from app.models.order_cancellation import OrderCancellation
from app.models.inventory import InventoryItem, StockMovement
from app.models.refund import Refund
from app.schemas.order_cancellation import OrderCancellationCreate, OrderCancellationResponse
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/order-cancellations", tags=["Module 28: Order Cancellation"])


@router.post("/{order_id}", response_model=OrderCancellationResponse, status_code=status.HTTP_201_CREATED)
def request_order_cancellation(
    order_id: int,
    payload: OrderCancellationCreate,
    current_user: User = Depends(require_permissions(Permission.ORDER_CANCEL.value)),
    db: Session = Depends(get_db)
):
    """
    Allow eligible customers and staff to request order cancellation.
    Validates cancellation eligibility rules (orders in DELIVERED state cannot be cancelled).
    Releases reserved stock back to available inventory.
    Initiates automatic refund if payment was already collected.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another customer's order")

    # Eligibility validation
    if order.status in ["DELIVERED", "CANCELLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be cancelled. Current status is '{order.status}'."
        )

    # Check for existing cancellation record
    existing_cancellation = db.query(OrderCancellation).filter(OrderCancellation.order_id == order_id).first()
    if existing_cancellation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cancellation request has already been filed for this order"
        )

    # Transition order status to CANCELLED
    old_status = order.status
    order.status = "CANCELLED"

    history = OrderStatusHistory(
        order_id=order.id,
        from_status=old_status,
        to_status="CANCELLED",
        notes=f"Order cancelled by {current_user.email}. Reason: {payload.reason}",
        changed_by_user_id=current_user.id
    )
    db.add(history)

    # 1. Release reserved inventory
    for item in order.items:
        inv_query = db.query(InventoryItem).filter(InventoryItem.product_id == item.product_id)
        if item.variant_id:
            inv_query = inv_query.filter(InventoryItem.variant_id == item.variant_id)
        inv = inv_query.first()
        if inv:
            qty_to_restore = min(inv.reserved_quantity, item.quantity)
            inv.reserved_quantity -= qty_to_restore
            inv.available_quantity += qty_to_restore

            movement = StockMovement(
                inventory_item_id=inv.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                warehouse_id=1,
                movement_type="RESERVE_RELEASE",
                quantity=qty_to_restore,
                balance_after=inv.available_quantity,
                reference_type="ORDER_CANCELLATION",
                reference_id=str(order.id),
                notes=f"Restored inventory due to order cancellation: {payload.reason}",
                performed_by_user_id=current_user.id
            )
            db.add(movement)

    # 2. Check refund initiation
    refund_triggered = False
    if order.payment_status == "PAID":
        refund_triggered = True
        refund = Refund(
            refund_number=f"REF-CAN-{order.id}-{int(order.total_amount)}",
            order_id=order.id,
            user_id=order.user_id,
            amount=order.total_amount,
            reason=f"Automatic refund upon order cancellation: {payload.reason}",
            status="COMPLETED",
            processed_by_user_id=current_user.id,
            admin_notes="Auto-issued via Order Cancellation Workflow"
        )
        order.payment_status = "REFUNDED"
        db.add(refund)

    cancellation = OrderCancellation(
        order_id=order.id,
        user_id=current_user.id,
        reason=payload.reason,
        status="COMPLETED",
        refund_initiated=refund_triggered,
        inventory_released=True,
        admin_notes=payload.admin_notes
    )
    db.add(cancellation)
    db.commit()
    db.refresh(cancellation)

    return cancellation


@router.get("/{order_id}", response_model=OrderCancellationResponse)
def get_order_cancellation_details(
    order_id: int,
    current_user: User = Depends(require_permissions(Permission.ORDERS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve cancellation record and outcome for an order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    cancellation = db.query(OrderCancellation).filter(OrderCancellation.order_id == order_id).first()
    if not cancellation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No cancellation record found for this order")

    return cancellation


@router.get("/", response_model=List[OrderCancellationResponse])
def list_cancellations(
    current_user: User = Depends(require_permissions(Permission.ORDERS_ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    List all order cancellation requests (Admin/Staff view).
    """
    cancellations = db.query(OrderCancellation).order_by(OrderCancellation.created_at.desc()).all()
    return cancellations

