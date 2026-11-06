import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.variant import ProductVariant
from app.models.inventory import InventoryItem, StockMovement
from app.models.order_return import ExchangeRequest
from app.schemas.return_exchange import (
    ExchangeRequestCreate, ExchangeReview, ExchangeRequestResponse
)
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/exchanges", tags=["Module 37: Exchange Management"])


@router.post("", response_model=ExchangeRequestResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ExchangeRequestResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_exchange_request(
    payload: ExchangeRequestCreate,
    current_user: User = Depends(require_permissions(Permission.EXCHANGES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 37: Create product exchange request.
    Validates replacement variant stock availability.
    """
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role == "CUSTOMER" and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot exchange items for another customer's order")

    orig_item = db.query(OrderItem).filter(
        OrderItem.id == payload.original_item_id,
        OrderItem.order_id == order.id
    ).first()
    if not orig_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original order item not found")

    # Validate replacement variant exists & has stock
    replacement = db.query(ProductVariant).filter(ProductVariant.id == payload.replacement_variant_id).first()
    if not replacement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replacement product variant not found")

    inv = db.query(InventoryItem).filter(InventoryItem.variant_id == replacement.id).first()
    if not inv:
        inv = db.query(InventoryItem).filter(InventoryItem.product_id == replacement.product_id).first()
    available = inv.available_quantity if inv else 0
    if available < payload.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Replacement variant '{replacement.sku}' has insufficient stock ({available} available, {payload.quantity} requested)"
        )

    exchange_num = f"EXC-{uuid.uuid4().hex[:8].upper()}"
    exchange = ExchangeRequest(
        exchange_number=exchange_num,
        order_id=order.id,
        user_id=current_user.id,
        original_item_id=orig_item.id,
        replacement_variant_id=replacement.id,
        quantity=payload.quantity,
        reason=payload.reason,
        status="REQUESTED"
    )
    db.add(exchange)
    db.commit()
    db.refresh(exchange)
    return exchange


@router.get("", response_model=List[ExchangeRequestResponse])
@router.get("/", response_model=List[ExchangeRequestResponse], include_in_schema=False)
def list_exchanges(
    order_id: Optional[int] = None,
    current_user: User = Depends(require_permissions(Permission.EXCHANGES_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve product exchange requests (scoped by role).
    """
    query = db.query(ExchangeRequest)
    if order_id:
        query = query.filter(ExchangeRequest.order_id == order_id)

    if current_user.role == "CUSTOMER":
        query = query.filter(ExchangeRequest.user_id == current_user.id)

    exchanges = query.order_by(ExchangeRequest.created_at.desc()).all()
    return exchanges


@router.get("/{exchange_id}", response_model=ExchangeRequestResponse)
def get_exchange_details(
    exchange_id: int,
    current_user: User = Depends(require_permissions(Permission.EXCHANGES_READ.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve exchange request details by ID.
    """
    exchange = db.query(ExchangeRequest).filter(ExchangeRequest.id == exchange_id).first()
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange request not found")

    if current_user.role == "CUSTOMER" and exchange.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return exchange


@router.patch("/{exchange_id}/review", response_model=ExchangeRequestResponse)
def review_exchange_request(
    exchange_id: int,
    payload: ExchangeReview,
    current_user: User = Depends(require_permissions(Permission.EXCHANGES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Approve or reject product exchange request (Staff/Admin).
    """
    exchange = db.query(ExchangeRequest).filter(ExchangeRequest.id == exchange_id).first()
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange request not found")

    new_status = payload.status.upper()
    valid_statuses = {"APPROVED", "REJECTED", "DISPATCHED", "COMPLETED"}
    if new_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid review status: {valid_statuses}")

    exchange.status = new_status
    if payload.admin_notes:
        exchange.admin_notes = payload.admin_notes

    db.commit()
    db.refresh(exchange)
    return exchange


@router.post("/{exchange_id}/dispatch", response_model=ExchangeRequestResponse)
def dispatch_replacement_item(
    exchange_id: int,
    current_user: User = Depends(require_permissions(Permission.EXCHANGES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Dispatch replacement goods for approved exchange, deducting replacement inventory.
    """
    exchange = db.query(ExchangeRequest).filter(ExchangeRequest.id == exchange_id).first()
    if not exchange:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exchange request not found")

    if exchange.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Exchange must be 'APPROVED' before dispatch")

    exchange.status = "DISPATCHED"

    # Deduct stock for replacement
    inv = db.query(InventoryItem).filter(InventoryItem.variant_id == exchange.replacement_variant_id).first()
    if not inv:
        replacement = db.query(ProductVariant).filter(ProductVariant.id == exchange.replacement_variant_id).first()
        if replacement:
            inv = db.query(InventoryItem).filter(InventoryItem.product_id == replacement.product_id).first()
    if inv and inv.available_quantity >= exchange.quantity:
        inv.available_quantity -= exchange.quantity
        inv.total_quantity -= exchange.quantity

        movement = StockMovement(
            inventory_item_id=inv.id,
            product_id=inv.product_id,
            variant_id=exchange.replacement_variant_id,
            warehouse_id=1,
            movement_type="EXCHANGE_OUT",
            quantity=exchange.quantity,
            balance_after=inv.available_quantity,
            reference_type="EXCHANGE_DISPATCH",
            reference_id=str(exchange.id),
            notes=f"Dispatched replacement items for Exchange #{exchange.exchange_number}",
            performed_by_user_id=current_user.id
        )
        db.add(movement)

    db.commit()
    db.refresh(exchange)
    return exchange
