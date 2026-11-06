from datetime import datetime, timezone
import uuid
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.supplier import Supplier
from app.models.warehouse import Warehouse, WarehouseInventory
from app.models.inventory import InventoryItem, StockMovement
from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POStatusHistory
from app.schemas.purchase_order import (
    POCreate, POResponse, POStatusUpdate, POReceiveRequest
)
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/purchase-orders", tags=["Module 44: Purchase Order Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("", response_model=POResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: POCreate,
    current_user: User = Depends(require_permissions(Permission.PURCHASE_ORDERS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Create a purchase order for a supplier with line items.
    """
    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if supplier.status != "APPROVED":
        raise HTTPException(status_code=400, detail=f"Cannot issue PO to unapproved supplier (status: {supplier.status})")

    warehouse = db.query(Warehouse).filter(Warehouse.id == payload.warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Purchase order must contain at least one item")

    # Generate PO Number: PO-YYYYMMDD-XXXX
    today_str = utc_now().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    po_number = f"PO-{today_str}-{unique_suffix}"

    total_cost = Decimal("0.00")
    po_items = []

    for item_in in payload.items:
        prod = db.query(Product).filter(Product.id == item_in.product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Product #{item_in.product_id} not found")

        if item_in.quantity_ordered <= 0:
            raise HTTPException(status_code=400, detail="Ordered quantity must be greater than zero")

        line_total = Decimal(str(item_in.unit_cost)) * item_in.quantity_ordered
        total_cost += line_total

        po_item = PurchaseOrderItem(
            product_id=item_in.product_id,
            variant_id=item_in.variant_id,
            quantity_ordered=item_in.quantity_ordered,
            quantity_received=0,
            unit_cost=item_in.unit_cost,
            total_cost=line_total
        )
        po_items.append(po_item)

    po = PurchaseOrder(
        po_number=po_number,
        supplier_id=payload.supplier_id,
        warehouse_id=payload.warehouse_id,
        created_by_user_id=current_user.id,
        status="DRAFT",
        total_cost=total_cost,
        expected_delivery_date=payload.expected_delivery_date,
        notes=payload.notes,
        items=po_items
    )
    db.add(po)
    db.flush()

    status_hist = POStatusHistory(
        purchase_order_id=po.id,
        changed_by_user_id=current_user.id,
        from_status=None,
        to_status="DRAFT",
        notes="Purchase order created in draft state."
    )
    db.add(status_hist)
    db.commit()
    db.refresh(po)
    return po


@router.get("", response_model=List[POResponse])
def list_purchase_orders(
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by PO status"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permissions(Permission.PURCHASE_ORDERS_READ.value)),
    db: Session = Depends(get_db)
):
    """List and filter purchase orders."""
    query = db.query(PurchaseOrder)
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if warehouse_id:
        query = query.filter(PurchaseOrder.warehouse_id == warehouse_id)
    if status_filter:
        query = query.filter(PurchaseOrder.status == status_filter.upper())

    return query.order_by(PurchaseOrder.created_at.desc()).limit(limit).all()


@router.get("/{po_id}", response_model=POResponse)
def get_purchase_order(
    po_id: int,
    current_user: User = Depends(require_permissions(Permission.PURCHASE_ORDERS_READ.value)),
    db: Session = Depends(get_db)
):
    """Get purchase order details with line items and status history."""
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return po


@router.patch("/{po_id}/status", response_model=POResponse)
def update_po_status(
    po_id: int,
    payload: POStatusUpdate,
    current_user: User = Depends(require_permissions(Permission.PURCHASE_ORDERS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Transition purchase order status (SUBMITTED, CANCELLED).
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    target_status = payload.status.upper()
    if target_status not in ["SUBMITTED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Invalid status transition. Use receive endpoint to mark received.")

    from_status = po.status
    po.status = target_status
    po.updated_at = utc_now()

    hist = POStatusHistory(
        purchase_order_id=po.id,
        changed_by_user_id=current_user.id,
        from_status=from_status,
        to_status=target_status,
        notes=payload.notes or f"PO transitioned to {target_status}"
    )
    db.add(hist)
    db.commit()
    db.refresh(po)
    return po


@router.post("/{po_id}/receive", response_model=POResponse)
def receive_purchase_order_stock(
    po_id: int,
    payload: POReceiveRequest,
    current_user: User = Depends(require_permissions(Permission.PURCHASE_ORDERS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Receive stock against purchase order items.
    Updates received quantities, automatically adds stock to InventoryItem and WarehouseInventory,
    and logs immutable StockMovement audit records.
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if po.status in ["CANCELLED", "RECEIVED"]:
        raise HTTPException(status_code=400, detail=f"Cannot receive stock on PO with status '{po.status}'")

    item_map = {item.id: item for item in po.items}

    for recv in payload.items:
        if recv.item_id not in item_map:
            raise HTTPException(status_code=404, detail=f"PO line item #{recv.item_id} not found on this PO")

        line = item_map[recv.item_id]
        if recv.quantity_to_receive <= 0:
            continue

        remaining_needed = line.quantity_ordered - line.quantity_received
        if recv.quantity_to_receive > remaining_needed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot receive {recv.quantity_to_receive} units. Only {remaining_needed} units pending for item #{line.id}"
            )

        line.quantity_received += recv.quantity_to_receive

        # 1. Update/Add to central InventoryItem
        inv = db.query(InventoryItem).filter(
            InventoryItem.product_id == line.product_id,
            InventoryItem.variant_id == line.variant_id
        ).first()

        if not inv:
            inv = InventoryItem(
                product_id=line.product_id,
                variant_id=line.variant_id,
                total_quantity=recv.quantity_to_receive,
                available_quantity=recv.quantity_to_receive,
                reserved_quantity=0
            )
            db.add(inv)
            db.flush()
        else:
            inv.total_quantity += recv.quantity_to_receive
            inv.available_quantity += recv.quantity_to_receive

        # 2. Update/Add to WarehouseInventory
        wh_inv = db.query(WarehouseInventory).filter(
            WarehouseInventory.warehouse_id == po.warehouse_id,
            WarehouseInventory.product_id == line.product_id,
            WarehouseInventory.variant_id == line.variant_id
        ).first()

        if not wh_inv:
            wh_inv = WarehouseInventory(
                warehouse_id=po.warehouse_id,
                product_id=line.product_id,
                variant_id=line.variant_id,
                quantity=recv.quantity_to_receive,
                aisle_location="Dock Receipt"
            )
            db.add(wh_inv)
        else:
            wh_inv.quantity += recv.quantity_to_receive

        # 3. If variant exists, update variant stock_quantity
        if line.variant_id:
            variant = db.query(ProductVariant).filter(ProductVariant.id == line.variant_id).first()
            if variant:
                variant.stock_quantity += recv.quantity_to_receive
                if variant.stock_quantity > 0:
                    variant.availability_status = "IN_STOCK"

        # 4. Record StockMovement
        movement = StockMovement(
            inventory_item_id=inv.id,
            product_id=line.product_id,
            variant_id=line.variant_id,
            warehouse_id=po.warehouse_id,
            performed_by_user_id=current_user.id,
            movement_type="ADDITION",
            quantity=recv.quantity_to_receive,
            balance_after=inv.available_quantity,
            reference_type="PURCHASE_ORDER",
            reference_id=po.po_number,
            notes=f"Stock received via Purchase Order {po.po_number}"
        )
        db.add(movement)

    # Determine updated PO status
    total_ordered = sum(item.quantity_ordered for item in po.items)
    total_received = sum(item.quantity_received for item in po.items)

    from_status = po.status
    if total_received >= total_ordered:
        po.status = "RECEIVED"
    elif total_received > 0:
        po.status = "PARTIALLY_RECEIVED"

    po.updated_at = utc_now()

    hist = POStatusHistory(
        purchase_order_id=po.id,
        changed_by_user_id=current_user.id,
        from_status=from_status,
        to_status=po.status,
        notes=payload.notes or f"Stock received. Progress: {total_received}/{total_ordered} units"
    )
    db.add(hist)
    db.commit()
    db.refresh(po)
    return po


@router.get("/supplier/{supplier_id}", response_model=List[POResponse])
def get_supplier_purchase_history(
    supplier_id: int,
    current_user: User = Depends(require_permissions(Permission.PURCHASE_ORDERS_READ.value)),
    db: Session = Depends(get_db)
):
    """Maintain and view complete purchase history for a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == supplier_id).order_by(PurchaseOrder.created_at.desc()).all()
