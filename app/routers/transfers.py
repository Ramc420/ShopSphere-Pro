import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.inventory import InventoryItem, StockMovement
from app.models.product import Product
from app.models.transfer import InventoryTransfer
from app.models.user import User
from app.models.variant import ProductVariant
from app.models.warehouse import Warehouse, WarehouseInventory
from app.schemas.transfer import TransferCreate, TransferDispatch, TransferReceive, TransferResponse

router = APIRouter(prefix="/transfers", tags=["Module 15: Inventory Transfers"])


def utc_now():
    return datetime.now(timezone.utc)


def serialize_transfer(t: InventoryTransfer) -> TransferResponse:
    return TransferResponse(
        id=t.id,
        transfer_number=t.transfer_number,
        source_warehouse_id=t.source_warehouse_id,
        destination_warehouse_id=t.destination_warehouse_id,
        product_id=t.product_id,
        variant_id=t.variant_id,
        requested_quantity=t.requested_quantity,
        dispatched_quantity=t.dispatched_quantity,
        received_quantity=t.received_quantity,
        status=t.status,
        notes=t.notes,
        requested_by_user_id=t.requested_by_user_id,
        dispatched_by_user_id=t.dispatched_by_user_id,
        received_by_user_id=t.received_by_user_id,
        dispatched_at=t.dispatched_at,
        received_at=t.received_at,
        created_at=t.created_at,
        updated_at=t.updated_at,
        source_warehouse_name=t.source_warehouse.name if t.source_warehouse else None,
        destination_warehouse_name=t.destination_warehouse.name if t.destination_warehouse else None,
        product_name=t.product.name if t.product else None,
    )


@router.post("", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer_request(
    payload: TransferCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Create an inventory stock transfer request between two warehouses.
    """
    if payload.source_warehouse_id == payload.destination_warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination warehouses must be distinct."
        )

    source_wh = db.query(Warehouse).filter(Warehouse.id == payload.source_warehouse_id).first()
    if not source_wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source warehouse not found")

    dest_wh = db.query(Warehouse).filter(Warehouse.id == payload.destination_warehouse_id).first()
    if not dest_wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination warehouse not found")

    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.variant_id:
        variant = db.query(ProductVariant).filter(
            ProductVariant.id == payload.variant_id,
            ProductVariant.product_id == payload.product_id
        ).first()
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product variant not found")

    # Generate unique transfer number
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    short_uuid = uuid.uuid4().hex[:6].upper()
    transfer_number = f"TRF-{today_str}-{short_uuid}"

    transfer = InventoryTransfer(
        transfer_number=transfer_number,
        source_warehouse_id=payload.source_warehouse_id,
        destination_warehouse_id=payload.destination_warehouse_id,
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        requested_quantity=payload.requested_quantity,
        dispatched_quantity=0,
        received_quantity=0,
        status="REQUESTED",
        notes=payload.notes,
        requested_by_user_id=current_user.id
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    log_user_activity(
        db,
        action="TRANSFER_REQUESTED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"transfer_id": transfer.id, "transfer_number": transfer.transfer_number}
    )

    return serialize_transfer(transfer)


@router.get("", response_model=List[TransferResponse])
def get_transfers(
    status: Optional[str] = Query(None, description="REQUESTED, DISPATCHED, RECEIVED, CANCELLED"),
    source_warehouse_id: Optional[int] = None,
    destination_warehouse_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    List and track inventory transfer requests and their current statuses.
    """
    stmt = db.query(InventoryTransfer)
    if status:
        stmt = stmt.filter(InventoryTransfer.status == status.upper())
    if source_warehouse_id:
        stmt = stmt.filter(InventoryTransfer.source_warehouse_id == source_warehouse_id)
    if destination_warehouse_id:
        stmt = stmt.filter(InventoryTransfer.destination_warehouse_id == destination_warehouse_id)

    transfers = stmt.order_by(InventoryTransfer.created_at.desc()).all()
    return [serialize_transfer(t) for t in transfers]


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer_by_id(
    transfer_id: int,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve inventory transfer details by ID.
    """
    t = db.query(InventoryTransfer).filter(InventoryTransfer.id == transfer_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")
    return serialize_transfer(t)


@router.post("/{transfer_id}/dispatch", response_model=TransferResponse)
def record_dispatch(
    transfer_id: int,
    payload: TransferDispatch,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Record dispatch of inventory from source warehouse.
    Deducts stock from source warehouse and records inventory movement.
    """
    t = db.query(InventoryTransfer).filter(InventoryTransfer.id == transfer_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    if t.status != "REQUESTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispatch transfer in status '{t.status}'. Must be 'REQUESTED'."
        )

    # Check warehouse inventory
    wh_inv = db.query(WarehouseInventory).filter(
        WarehouseInventory.warehouse_id == t.source_warehouse_id,
        WarehouseInventory.product_id == t.product_id,
        WarehouseInventory.variant_id == t.variant_id
    ).first()

    available_wh = wh_inv.quantity - wh_inv.reserved_quantity if wh_inv else 0
    if available_wh < payload.dispatched_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock in source warehouse. Available: {available_wh}, Requested dispatch: {payload.dispatched_quantity}"
        )

    # Reduce source warehouse quantity
    wh_inv.quantity -= payload.dispatched_quantity
    source_wh = db.query(Warehouse).filter(Warehouse.id == t.source_warehouse_id).first()
    if source_wh:
        source_wh.current_utilization = max(0, source_wh.current_utilization - payload.dispatched_quantity)

    # Record StockMovement
    inv_item = db.query(InventoryItem).filter(
        InventoryItem.product_id == t.product_id,
        InventoryItem.variant_id == t.variant_id
    ).first()

    if inv_item:
        movement = StockMovement(
            inventory_item_id=inv_item.id,
            product_id=t.product_id,
            variant_id=t.variant_id,
            warehouse_id=t.source_warehouse_id,
            movement_type="TRANSFER_OUT",
            quantity=-payload.dispatched_quantity,
            balance_after=wh_inv.quantity,
            reference_type="INVENTORY_TRANSFER",
            reference_id=t.transfer_number,
            notes=payload.notes or f"Dispatched via transfer {t.transfer_number}",
            performed_by_user_id=current_user.id
        )
        db.add(movement)

    t.dispatched_quantity = payload.dispatched_quantity
    t.dispatched_by_user_id = current_user.id
    t.dispatched_at = utc_now()
    t.status = "DISPATCHED"
    if payload.notes:
        t.notes = f"{t.notes or ''}\nDispatch: {payload.notes}".strip()

    db.commit()
    db.refresh(t)

    log_user_activity(
        db,
        action="TRANSFER_DISPATCHED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"transfer_id": t.id, "dispatched_quantity": payload.dispatched_quantity}
    )

    return serialize_transfer(t)


@router.post("/{transfer_id}/receive", response_model=TransferResponse)
def record_receipt(
    transfer_id: int,
    payload: TransferReceive,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Record receipt of inventory at destination warehouse.
    Increases destination warehouse inventory and records stock movement.
    """
    t = db.query(InventoryTransfer).filter(InventoryTransfer.id == transfer_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    if t.status != "DISPATCHED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot receive transfer in status '{t.status}'. Must be 'DISPATCHED'."
        )

    # Check destination warehouse capacity
    dest_wh = db.query(Warehouse).filter(Warehouse.id == t.destination_warehouse_id).first()
    if not dest_wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination warehouse not found")

    if dest_wh.current_utilization + payload.received_quantity > dest_wh.capacity_units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Destination warehouse capacity exceeded. Capacity: {dest_wh.capacity_units}, Current: {dest_wh.current_utilization}"
        )

    dest_wh_inv = db.query(WarehouseInventory).filter(
        WarehouseInventory.warehouse_id == t.destination_warehouse_id,
        WarehouseInventory.product_id == t.product_id,
        WarehouseInventory.variant_id == t.variant_id
    ).first()

    if dest_wh_inv:
        dest_wh_inv.quantity += payload.received_quantity
    else:
        dest_wh_inv = WarehouseInventory(
            warehouse_id=t.destination_warehouse_id,
            product_id=t.product_id,
            variant_id=t.variant_id,
            quantity=payload.received_quantity,
            reserved_quantity=0
        )
        db.add(dest_wh_inv)

    dest_wh.current_utilization += payload.received_quantity

    inv_item = db.query(InventoryItem).filter(
        InventoryItem.product_id == t.product_id,
        InventoryItem.variant_id == t.variant_id
    ).first()

    if inv_item:
        movement = StockMovement(
            inventory_item_id=inv_item.id,
            product_id=t.product_id,
            variant_id=t.variant_id,
            warehouse_id=t.destination_warehouse_id,
            movement_type="TRANSFER_IN",
            quantity=payload.received_quantity,
            balance_after=dest_wh_inv.quantity,
            reference_type="INVENTORY_TRANSFER",
            reference_id=t.transfer_number,
            notes=payload.notes or f"Received via transfer {t.transfer_number}",
            performed_by_user_id=current_user.id
        )
        db.add(movement)

    t.received_quantity = payload.received_quantity
    t.received_by_user_id = current_user.id
    t.received_at = utc_now()
    t.status = "RECEIVED"
    if payload.notes:
        t.notes = f"{t.notes or ''}\nReceipt: {payload.notes}".strip()

    db.commit()
    db.refresh(t)

    log_user_activity(
        db,
        action="TRANSFER_RECEIVED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"transfer_id": t.id, "received_quantity": payload.received_quantity}
    )

    return serialize_transfer(t)


@router.post("/{transfer_id}/cancel", response_model=TransferResponse)
def cancel_transfer(
    transfer_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Cancel an unfulfilled transfer request.
    """
    t = db.query(InventoryTransfer).filter(InventoryTransfer.id == transfer_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found")

    if t.status in ("RECEIVED", "CANCELLED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel transfer in status '{t.status}'."
        )

    # If already dispatched, restore to source warehouse
    if t.status == "DISPATCHED" and t.dispatched_quantity > 0:
        wh_inv = db.query(WarehouseInventory).filter(
            WarehouseInventory.warehouse_id == t.source_warehouse_id,
            WarehouseInventory.product_id == t.product_id,
            WarehouseInventory.variant_id == t.variant_id
        ).first()
        if wh_inv:
            wh_inv.quantity += t.dispatched_quantity
        source_wh = db.query(Warehouse).filter(Warehouse.id == t.source_warehouse_id).first()
        if source_wh:
            source_wh.current_utilization += t.dispatched_quantity

    t.status = "CANCELLED"
    db.commit()
    db.refresh(t)

    return serialize_transfer(t)

