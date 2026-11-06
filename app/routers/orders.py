from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.inventory import InventoryItem, StockMovement
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.user import User
from app.schemas.order import (
    OrderItemResponse,
    OrderResponse,
    OrderStatusHistoryResponse,
    OrderStatusUpdate,
)

router = APIRouter(prefix="/orders", tags=["Module 25: Order Management"])


def utc_now():
    return datetime.now(timezone.utc)


def serialize_order(order: Order) -> OrderResponse:
    item_responses = [
        OrderItemResponse(
            id=i.id,
            order_id=i.order_id,
            product_id=i.product_id,
            variant_id=i.variant_id,
            product_name=i.product_name,
            sku=i.sku,
            unit_price=float(i.unit_price),
            quantity=i.quantity,
            subtotal=float(i.subtotal)
        )
        for i in order.items
    ]

    hist_responses = [
        OrderStatusHistoryResponse(
            id=h.id,
            order_id=h.order_id,
            from_status=h.from_status,
            to_status=h.to_status,
            notes=h.notes,
            changed_by_user_id=h.changed_by_user_id,
            created_at=h.created_at
        )
        for h in order.status_history
    ]

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        shipping_address_id=order.shipping_address_id,
        billing_address_id=order.billing_address_id,
        shipping_address_snapshot=order.shipping_address_snapshot,
        billing_address_snapshot=order.billing_address_snapshot,
        status=order.status,
        payment_status=order.payment_status,
        subtotal_amount=float(order.subtotal_amount),
        discount_amount=float(order.discount_amount),
        tax_amount=float(order.tax_amount),
        shipping_amount=float(order.shipping_amount),
        total_amount=float(order.total_amount),
        coupon_code=order.coupon_code,
        shipping_method_code=order.shipping_method_code,
        notes=order.notes,
        items=item_responses,
        status_history=hist_responses,
        created_at=order.created_at,
        updated_at=order.updated_at
    )


@router.get("", response_model=List[OrderResponse])
def get_orders(
    user_id: Optional[int] = Query(None, description="Filter by customer user ID (Admin/Employee only)"),
    status: Optional[str] = Query(None, description="PENDING, CONFIRMED, PROCESSING, SHIPPED, DELIVERED, CANCELLED"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search and filter customer orders.
    Customers can only view their own orders; Employees and Admins can view all orders.
    """
    stmt = db.query(Order)

    if current_user.role == UserRole.CUSTOMER.value:
        stmt = stmt.filter(Order.user_id == current_user.id)
    else:
        if user_id:
            stmt = stmt.filter(Order.user_id == user_id)

    if status:
        stmt = stmt.filter(Order.status == status.upper())

    orders = stmt.order_by(Order.created_at.desc()).limit(limit).all()
    return [serialize_order(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve single order details, order items, addresses, price summaries, and status history.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == UserRole.CUSTOMER.value and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this order.")

    return serialize_order(order)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Transition order status and maintain immutable status history.
    If the order is CANCELLED, releases reserved inventory back to available stock.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    new_status = payload.status.upper()
    old_status = order.status

    if old_status == new_status:
        return serialize_order(order)

    # If cancelling, release reserved inventory
    if new_status == "CANCELLED" and old_status != "CANCELLED":
        for item in order.items:
            inv = db.query(InventoryItem).filter(
                InventoryItem.product_id == item.product_id,
                InventoryItem.variant_id == item.variant_id
            ).first()
            if inv:
                # Release reserved back to available
                release_qty = min(inv.reserved_quantity, item.quantity)
                inv.reserved_quantity -= release_qty
                inv.available_quantity += release_qty

                movement = StockMovement(
                    inventory_item_id=inv.id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    movement_type="RELEASE",
                    quantity=release_qty,
                    balance_after=inv.available_quantity,
                    reference_type="ORDER_CANCELLATION",
                    reference_id=order.order_number,
                    notes=f"Released upon order {order.order_number} cancellation",
                    performed_by_user_id=current_user.id
                )
                db.add(movement)

    # Record history
    history = OrderStatusHistory(
        order_id=order.id,
        from_status=old_status,
        to_status=new_status,
        notes=payload.notes or f"Status changed from {old_status} to {new_status}",
        changed_by_user_id=current_user.id
    )
    db.add(history)

    order.status = new_status
    order.updated_at = utc_now()
    db.commit()
    db.refresh(order)

    log_user_activity(
        db,
        action="ORDER_STATUS_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"order_id": order.id, "from": old_status, "to": new_status}
    )

    return serialize_order(order)


@router.get("/{order_id}/history", response_model=List[OrderStatusHistoryResponse])
def get_order_status_history(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve chronological audit trail of order status transitions.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == UserRole.CUSTOMER.value and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return [
        OrderStatusHistoryResponse(
            id=h.id,
            order_id=h.order_id,
            from_status=h.from_status,
            to_status=h.to_status,
            notes=h.notes,
            changed_by_user_id=h.changed_by_user_id,
            created_at=h.created_at
        )
        for h in order.status_history
    ]

