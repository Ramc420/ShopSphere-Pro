from typing import List, Dict, Set
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderStatusHistory
from app.models.inventory import InventoryItem, StockMovement
from app.schemas.order import OrderResponse, OrderStatusHistoryResponse
from app.schemas.order_status import OrderStatusTransitionRequest, PermittedTransitionsResponse
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/order-status", tags=["Module 27: Order Status Management"])

# Strict permitted status transition state machine
PERMITTED_TRANSITIONS: Dict[str, Set[str]] = {
    "PENDING": {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"PROCESSING", "CANCELLED"},
    "PROCESSING": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"DELIVERED", "CANCELLED"},
    "DELIVERED": set(),
    "CANCELLED": set()
}


@router.get("/permitted-transitions/{order_id}", response_model=PermittedTransitionsResponse)
def get_permitted_transitions(
    order_id: int,
    current_user: User = Depends(require_permissions(Permission.ORDER_STATUS_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve permitted status transitions based on current order state.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    allowed = sorted(list(PERMITTED_TRANSITIONS.get(order.status, set())))
    return PermittedTransitionsResponse(
        current_status=order.status,
        permitted_next_statuses=allowed,
        order_id=order.id
    )


@router.post("/transition/{order_id}", response_model=OrderResponse)
def execute_order_status_transition(
    order_id: int,
    payload: OrderStatusTransitionRequest,
    current_user: User = Depends(require_permissions(Permission.ORDER_STATUS_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Validate and execute permitted order status transitions.
    Records transition event in OrderStatusHistory.
    Automatically reconciles reserved stock if transitioning to CANCELLED.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    target_status = payload.to_status.upper()
    allowed_transitions = PERMITTED_TRANSITIONS.get(order.status, set())

    if target_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition: Cannot transition order from '{order.status}' to '{target_status}'. Permitted: {sorted(list(allowed_transitions))}"
        )

    old_status = order.status
    order.status = target_status

    # Record history
    history = OrderStatusHistory(
        order_id=order.id,
        from_status=old_status,
        to_status=target_status,
        notes=payload.notes or f"Transitioned from {old_status} to {target_status} by {current_user.email}",
        changed_by_user_id=current_user.id
    )
    db.add(history)

    # Reconcile inventory if cancelled
    if target_status == "CANCELLED":
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
                    notes=f"Released reserved inventory upon status transition to CANCELLED",
                    performed_by_user_id=current_user.id
                )
                db.add(movement)

    db.commit()
    db.refresh(order)
    return order


@router.get("/history/{order_id}", response_model=List[OrderStatusHistoryResponse])
def get_order_status_history(
    order_id: int,
    current_user: User = Depends(require_permissions(Permission.ORDERS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve full audit processing history and status timeline for an order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    history = db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.created_at.asc()).all()
    return history

