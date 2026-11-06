import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.order_return import ReturnRequest, ReturnItem
from app.models.inventory import InventoryItem, StockMovement
from app.schemas.return_exchange import (
    ReturnRequestCreate, ReturnReview, ReturnRequestResponse
)
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/returns", tags=["Module 36: Return Management"])


@router.post("", response_model=ReturnRequestResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ReturnRequestResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def request_order_return(
    payload: ReturnRequestCreate,
    current_user: User = Depends(require_permissions(Permission.RETURNS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 36: Allow eligible customers to request item returns.
    Validates order status (must be DELIVERED) and validates order item quantities.
    """
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot request return for another customer's order")

    if order.status != "DELIVERED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is not eligible for return. Order must be 'DELIVERED', but current status is '{order.status}'."
        )

    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one item must be specified for return")

    return_number = f"RET-{uuid.uuid4().hex[:8].upper()}"
    ret = ReturnRequest(
        return_number=return_number,
        order_id=order.id,
        user_id=current_user.id,
        reason=payload.reason,
        status="REQUESTED"
    )
    db.add(ret)
    db.flush()

    for item_data in payload.items:
        order_item = db.query(OrderItem).filter(
            OrderItem.id == item_data.order_item_id,
            OrderItem.order_id == order.id
        ).first()
        if not order_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order item #{item_data.order_item_id} not found in order #{order.id}"
            )
        if item_data.quantity > order_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Return quantity ({item_data.quantity}) exceeds ordered quantity ({order_item.quantity}) for item #{order_item.id}"
            )

        ret_item = ReturnItem(
            return_request_id=ret.id,
            order_item_id=order_item.id,
            quantity=item_data.quantity,
            item_condition=item_data.item_condition
        )
        db.add(ret_item)

    db.commit()
    db.refresh(ret)
    return ret


@router.get("", response_model=List[ReturnRequestResponse])
@router.get("/", response_model=List[ReturnRequestResponse], include_in_schema=False)
def list_returns(
    order_id: Optional[int] = None,
    current_user: User = Depends(require_permissions(Permission.RETURNS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve return requests (scoped by user role).
    """
    query = db.query(ReturnRequest)
    if order_id:
        query = query.filter(ReturnRequest.order_id == order_id)

    if current_user.role == "CUSTOMER":
        query = query.filter(ReturnRequest.user_id == current_user.id)

    returns = query.order_by(ReturnRequest.created_at.desc()).all()
    return returns


@router.get("/{return_id}", response_model=ReturnRequestResponse)
def get_return_details(
    return_id: int,
    current_user: User = Depends(require_permissions(Permission.RETURNS_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve return request details by ID.
    """
    ret = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found")

    if current_user.role == "CUSTOMER" and ret.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ret


@router.patch("/{return_id}/review", response_model=ReturnRequestResponse)
def review_return_request(
    return_id: int,
    payload: ReturnReview,
    current_user: User = Depends(require_permissions(Permission.RETURNS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Approve or reject customer return request (Admin/Staff only).
    """
    ret = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found")

    new_status = payload.status.upper()
    valid_statuses = {"APPROVED", "REJECTED", "ITEMS_RECEIVED", "REFUNDED", "CANCELLED"}
    if new_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid review status: {valid_statuses}")

    ret.status = new_status
    if payload.admin_notes:
        ret.admin_notes = payload.admin_notes

    db.commit()
    db.refresh(ret)
    return ret


@router.post("/{return_id}/receive", response_model=ReturnRequestResponse)
def receive_returned_goods(
    return_id: int,
    current_user: User = Depends(require_permissions(Permission.RETURNS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Mark returned items physically received at warehouse and increment stock.
    """
    ret = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not ret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found")

    ret.status = "ITEMS_RECEIVED"

    # Restock unopened/usable items
    for item in ret.items:
        order_item = item.order_item
        if order_item and item.item_condition in ["UNOPENED", "OPEN_BOX"]:
            inv_query = db.query(InventoryItem).filter(InventoryItem.product_id == order_item.product_id)
            if order_item.variant_id:
                inv_query = inv_query.filter(InventoryItem.variant_id == order_item.variant_id)
            inv = inv_query.first()
            if inv:
                inv.available_quantity += item.quantity
                inv.total_quantity += item.quantity

                movement = StockMovement(
                    inventory_item_id=inv.id,
                    product_id=order_item.product_id,
                    variant_id=order_item.variant_id,
                    warehouse_id=1,
                    movement_type="RETURN_IN",
                    quantity=item.quantity,
                    balance_after=inv.available_quantity,
                    reference_type="RETURN_RECEIPT",
                    reference_id=str(ret.id),
                    notes=f"Restocked {item.quantity} units from Return #{ret.return_number}",
                    performed_by_user_id=current_user.id
                )
                db.add(movement)

    db.commit()
    db.refresh(ret)
    return ret
