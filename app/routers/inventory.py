from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.inventory import InventoryItem, StockMovement
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.schemas.inventory import (
    InventoryItemResponse,
    StockAdditionRequest,
    StockMovementResponse,
    StockReductionRequest,
    StockReleaseRequest,
    StockReservationRequest,
)

router = APIRouter(prefix="/inventory", tags=["Module 13: Inventory Management"])


def get_or_create_inventory(db: Session, product_id: int, variant_id: Optional[int] = None) -> InventoryItem:
    item = db.query(InventoryItem).filter(
        InventoryItem.product_id == product_id,
        InventoryItem.variant_id == variant_id
    ).first()

    if not item:
        # Check if product or variant exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        initial_qty = 0
        threshold = 5
        if variant_id:
            variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
            if not variant:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
            initial_qty = variant.stock_quantity
            threshold = variant.low_stock_threshold

        item = InventoryItem(
            product_id=product_id,
            variant_id=variant_id,
            total_quantity=initial_qty,
            available_quantity=initial_qty,
            reserved_quantity=0,
            low_stock_threshold=threshold
        )
        db.add(item)
        db.flush()

    return item


def compute_avail_status(item: InventoryItem) -> str:
    if item.available_quantity <= 0:
        return "OUT_OF_STOCK"
    elif item.available_quantity <= item.low_stock_threshold:
        return "LOW_STOCK"
    return "IN_STOCK"


def serialize_inventory(item: InventoryItem) -> InventoryItemResponse:
    return InventoryItemResponse(
        id=item.id,
        product_id=item.product_id,
        variant_id=item.variant_id,
        total_quantity=item.total_quantity,
        available_quantity=item.available_quantity,
        reserved_quantity=item.reserved_quantity,
        low_stock_threshold=item.low_stock_threshold,
        availability_status=compute_avail_status(item),
        updated_at=item.updated_at
    )


@router.get("/product/{product_id}", response_model=List[InventoryItemResponse])
def get_inventory_by_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve inventory quantities (total, available, reserved) for a product and its variants.
    """
    items = db.query(InventoryItem).filter(InventoryItem.product_id == product_id).all()
    if not items:
        # Create default root entry
        item = get_or_create_inventory(db, product_id, None)
        db.commit()
        db.refresh(item)
        items = [item]

    return [serialize_inventory(i) for i in items]


@router.get("/variant/{variant_id}", response_model=InventoryItemResponse)
def get_inventory_by_variant(
    variant_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve stock quantities for a specific variant.
    """
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    item = get_or_create_inventory(db, variant.product_id, variant.id)
    db.commit()
    db.refresh(item)
    return serialize_inventory(item)


@router.post("/product/{product_id}/add", response_model=InventoryItemResponse)
def record_stock_addition(
    product_id: int,
    payload: StockAdditionRequest,
    variant_id: Optional[int] = Query(None, description="Optional variant ID"),
    request: Request = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Record stock addition (PO receive, restock, return).
    Increases total and available stock quantities and logs movement.
    """
    item = get_or_create_inventory(db, product_id, variant_id)

    item.total_quantity += payload.quantity
    item.available_quantity += payload.quantity

    # Sync variant model stock if variant
    if variant_id:
        v = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if v:
            v.stock_quantity = item.total_quantity
            v.availability_status = compute_avail_status(item)

    movement = StockMovement(
        inventory_item_id=item.id,
        product_id=product_id,
        variant_id=variant_id,
        warehouse_id=payload.warehouse_id,
        movement_type="ADDITION",
        quantity=payload.quantity,
        balance_after=item.total_quantity,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        notes=payload.notes,
        performed_by_user_id=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(item)

    log_user_activity(
        db,
        action="STOCK_ADDITION",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"product_id": product_id, "variant_id": variant_id, "added": payload.quantity}
    )

    return serialize_inventory(item)


@router.post("/product/{product_id}/reduce", response_model=InventoryItemResponse)
def record_stock_reduction(
    product_id: int,
    payload: StockReductionRequest,
    variant_id: Optional[int] = Query(None, description="Optional variant ID"),
    request: Request = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Record stock reduction (damage, write-off, shrinkage).
    Prevents negative inventory: rejects if requested reduction exceeds available stock.
    """
    item = get_or_create_inventory(db, product_id, variant_id)

    if payload.quantity > item.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reduce {payload.quantity} units. Only {item.available_quantity} available in stock (negative inventory prevented)."
        )

    item.total_quantity -= payload.quantity
    item.available_quantity -= payload.quantity

    if variant_id:
        v = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if v:
            v.stock_quantity = item.total_quantity
            v.availability_status = compute_avail_status(item)

    movement = StockMovement(
        inventory_item_id=item.id,
        product_id=product_id,
        variant_id=variant_id,
        warehouse_id=payload.warehouse_id,
        movement_type="REDUCTION",
        quantity=-payload.quantity,
        balance_after=item.total_quantity,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        notes=payload.notes,
        performed_by_user_id=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(item)

    log_user_activity(
        db,
        action="STOCK_REDUCTION",
        user_id=current_user.id,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
        details={"product_id": product_id, "reduced": payload.quantity}
    )

    return serialize_inventory(item)


@router.post("/product/{product_id}/reserve", response_model=InventoryItemResponse)
def reserve_stock(
    product_id: int,
    payload: StockReservationRequest,
    variant_id: Optional[int] = Query(None, description="Optional variant ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reserve available stock for a pending checkout or cart.
    Prevents negative inventory: cannot reserve more than currently available.
    """
    item = get_or_create_inventory(db, product_id, variant_id)

    if payload.quantity > item.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock to reserve {payload.quantity} units. Available: {item.available_quantity}"
        )

    item.available_quantity -= payload.quantity
    item.reserved_quantity += payload.quantity

    movement = StockMovement(
        inventory_item_id=item.id,
        product_id=product_id,
        variant_id=variant_id,
        movement_type="RESERVATION",
        quantity=payload.quantity,
        balance_after=item.available_quantity,
        reference_type="ORDER_RESERVATION",
        reference_id=payload.reference_id,
        notes=payload.notes,
        performed_by_user_id=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(item)

    return serialize_inventory(item)


@router.post("/product/{product_id}/release", response_model=InventoryItemResponse)
def release_reserved_stock(
    product_id: int,
    payload: StockReleaseRequest,
    variant_id: Optional[int] = Query(None, description="Optional variant ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Release previously reserved stock back to available stock.
    """
    item = get_or_create_inventory(db, product_id, variant_id)

    if payload.quantity > item.reserved_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot release {payload.quantity} units. Only {item.reserved_quantity} currently reserved."
        )

    item.reserved_quantity -= payload.quantity
    item.available_quantity += payload.quantity

    movement = StockMovement(
        inventory_item_id=item.id,
        product_id=product_id,
        variant_id=variant_id,
        movement_type="RELEASE",
        quantity=payload.quantity,
        balance_after=item.available_quantity,
        reference_type="ORDER_CANCELLATION",
        reference_id=payload.reference_id,
        notes=payload.notes,
        performed_by_user_id=current_user.id
    )
    db.add(movement)
    db.commit()
    db.refresh(item)

    return serialize_inventory(item)


@router.get("/movements/all", response_model=List[StockMovementResponse])
def get_all_stock_movements(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve inventory audit log of stock movements (additions, reductions, reservations).
    """
    stmt = db.query(StockMovement)
    if product_id:
        stmt = stmt.filter(StockMovement.product_id == product_id)
    return stmt.order_by(StockMovement.created_at.desc()).limit(limit).all()

