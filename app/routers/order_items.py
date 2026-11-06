from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderItem
from app.schemas.order_item import OrderItemDetailResponse, OrderItemFulfillmentUpdate
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/orders", tags=["Module 26: Order Item Management"])


@router.get("/{order_id}/items", response_model=List[OrderItemDetailResponse])
def get_order_items(
    order_id: int,
    current_user: User = Depends(require_permissions(Permission.ORDER_ITEMS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve product and variant details, pricing, descriptions, and fulfillment status for order items.
    Customers can only view items for their own orders; staff can view any.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access items for another customer's order")

    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return items


@router.get("/{order_id}/items/{item_id}", response_model=OrderItemDetailResponse)
def get_single_order_item(
    order_id: int,
    item_id: int,
    current_user: User = Depends(require_permissions(Permission.ORDER_ITEMS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve an individual order item by ID.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    item = db.query(OrderItem).filter(OrderItem.id == item_id, OrderItem.order_id == order_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")

    return item


@router.patch("/{order_id}/items/{item_id}/fulfillment", response_model=OrderItemDetailResponse)
def update_item_fulfillment_status(
    order_id: int,
    item_id: int,
    payload: OrderItemFulfillmentUpdate,
    current_user: User = Depends(require_permissions(Permission.ORDER_ITEMS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Maintain item-level fulfillment status (PENDING, PROCESSING, FULFILLED, CANCELLED, RETURNED).
    Restricted to staff roles.
    """
    item = db.query(OrderItem).filter(OrderItem.id == item_id, OrderItem.order_id == order_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found")

    valid_statuses = {"PENDING", "PROCESSING", "FULFILLED", "CANCELLED", "RETURNED"}
    if payload.fulfillment_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid fulfillment status. Allowed: {valid_statuses}"
        )

    item.fulfillment_status = payload.fulfillment_status
    db.commit()
    db.refresh(item)
    return item

