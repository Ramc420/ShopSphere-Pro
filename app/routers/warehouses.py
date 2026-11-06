from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.models.warehouse import Warehouse, WarehouseInventory
from app.schemas.common import MessageResponse
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseInventoryResponse,
    WarehouseResponse,
    WarehouseStockAssignRequest,
    WarehouseUpdate,
)

router = APIRouter(prefix="/warehouses", tags=["Module 14: Warehouse Management"])


def serialize_warehouse(w: Warehouse) -> WarehouseResponse:
    pct = round((w.current_utilization / w.capacity_units * 100), 2) if w.capacity_units > 0 else 0.0
    return WarehouseResponse(
        id=w.id,
        code=w.code,
        name=w.name,
        address_line1=w.address_line1,
        city=w.city,
        state_province=w.state_province,
        postal_code=w.postal_code,
        country=w.country,
        capacity_units=w.capacity_units,
        current_utilization=w.current_utilization,
        utilization_percentage=pct,
        status=w.status,
        manager_id=w.manager_id,
        created_at=w.created_at,
        updated_at=w.updated_at
    )


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Create a new warehouse facility. Restricts access to ADMIN and SUPER_ADMIN roles.
    """
    code_clean = payload.code.strip().upper()
    existing = db.query(Warehouse).filter(Warehouse.code == code_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Warehouse code '{code_clean}' already exists.")

    wh = Warehouse(
        code=code_clean,
        name=payload.name.strip(),
        address_line1=payload.address_line1.strip(),
        city=payload.city.strip(),
        state_province=payload.state_province.strip(),
        postal_code=payload.postal_code.strip(),
        country=payload.country.strip(),
        capacity_units=payload.capacity_units,
        current_utilization=0,
        status=payload.status.upper(),
        manager_id=payload.manager_id
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)

    log_user_activity(
        db,
        action="WAREHOUSE_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"warehouse_id": wh.id, "code": wh.code, "capacity": wh.capacity_units}
    )

    return serialize_warehouse(wh)


@router.get("", response_model=List[WarehouseResponse])
def get_warehouses(
    status: Optional[str] = Query(None, description="ACTIVE, INACTIVE, MAINTENANCE"),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    List all warehouses with current capacity utilization. Access restricted by role.
    """
    stmt = db.query(Warehouse)
    if status:
        stmt = stmt.filter(Warehouse.status == status.upper())
    warehouses = stmt.order_by(Warehouse.id.asc()).all()
    return [serialize_warehouse(w) for w in warehouses]


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse_by_id(
    warehouse_id: int,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve warehouse details by ID. Access restricted by role.
    """
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return serialize_warehouse(wh)


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Update warehouse facility properties, capacity bounds, and operating status.
    """
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    if payload.capacity_units is not None and payload.capacity_units < wh.current_utilization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reduce capacity to {payload.capacity_units}. Current utilization is {wh.current_utilization} units."
        )

    for field, val in payload.model_dump(exclude_unset=True).items():
        if val is not None:
            if isinstance(val, str):
                setattr(wh, field, val.strip())
            else:
                setattr(wh, field, val)

    db.commit()
    db.refresh(wh)

    log_user_activity(
        db,
        action="WAREHOUSE_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"warehouse_id": wh.id}
    )

    return serialize_warehouse(wh)


@router.post("/{warehouse_id}/stock", response_model=WarehouseInventoryResponse, status_code=status.HTTP_201_CREATED)
def assign_stock_to_warehouse(
    warehouse_id: int,
    payload: WarehouseStockAssignRequest,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Associate inventory with a warehouse facility.
    Validates warehouse status and enforces capacity restrictions.
    """
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    if wh.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign stock: Warehouse status is '{wh.status}' (must be ACTIVE)."
        )

    # Validate Product
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Validate Variant if provided
    variant = None
    if payload.variant_id:
        variant = db.query(ProductVariant).filter(ProductVariant.id == payload.variant_id).first()
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    # Check capacity limit
    new_utilization = wh.current_utilization + payload.quantity
    if new_utilization > wh.capacity_units:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Warehouse capacity exceeded. Capacity: {wh.capacity_units}, Current: {wh.current_utilization}, Attempted addition: {payload.quantity}"
        )

    existing_entry = db.query(WarehouseInventory).filter(
        WarehouseInventory.warehouse_id == warehouse_id,
        WarehouseInventory.product_id == payload.product_id,
        WarehouseInventory.variant_id == payload.variant_id
    ).first()

    if existing_entry:
        existing_entry.quantity += payload.quantity
        if payload.aisle_location:
            existing_entry.aisle_location = payload.aisle_location.strip()
        inv_record = existing_entry
    else:
        inv_record = WarehouseInventory(
            warehouse_id=warehouse_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity,
            aisle_location=payload.aisle_location.strip() if payload.aisle_location else None
        )
        db.add(inv_record)

    # Update warehouse utilization
    wh.current_utilization = new_utilization
    db.commit()
    db.refresh(inv_record)

    sku_val = variant.sku if variant else product.base_sku
    return WarehouseInventoryResponse(
        id=inv_record.id,
        warehouse_id=inv_record.warehouse_id,
        product_id=inv_record.product_id,
        variant_id=inv_record.variant_id,
        product_name=product.name,
        sku=sku_val,
        quantity=inv_record.quantity,
        reserved_quantity=inv_record.reserved_quantity,
        aisle_location=inv_record.aisle_location,
        updated_at=inv_record.updated_at
    )


@router.get("/{warehouse_id}/stock", response_model=List[WarehouseInventoryResponse])
def get_warehouse_level_stock(
    warehouse_id: int,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve warehouse-level stock quantities and aisle/bin locations.
    Restricted to authorized employee and administrator roles.
    """
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    items = (
        db.query(WarehouseInventory)
        .options(joinedload(WarehouseInventory.product), joinedload(WarehouseInventory.variant))
        .filter(WarehouseInventory.warehouse_id == warehouse_id)
        .all()
    )

    results = []
    for item in items:
        sku_val = item.variant.sku if item.variant else (item.product.base_sku if item.product else None)
        p_name = item.product.name if item.product else None
        results.append(
            WarehouseInventoryResponse(
                id=item.id,
                warehouse_id=item.warehouse_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=p_name,
                sku=sku_val,
                quantity=item.quantity,
                reserved_quantity=item.reserved_quantity,
                aisle_location=item.aisle_location,
                updated_at=item.updated_at
            )
        )
    return results


@router.get("/product/{product_id}/distribution", response_model=List[WarehouseInventoryResponse])
def get_product_warehouse_distribution(
    product_id: int,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve inventory distribution across all warehouses for a given product.
    """
    items = (
        db.query(WarehouseInventory)
        .options(joinedload(WarehouseInventory.product), joinedload(WarehouseInventory.variant))
        .filter(WarehouseInventory.product_id == product_id)
        .all()
    )

    results = []
    for item in items:
        sku_val = item.variant.sku if item.variant else (item.product.base_sku if item.product else None)
        p_name = item.product.name if item.product else None
        results.append(
            WarehouseInventoryResponse(
                id=item.id,
                warehouse_id=item.warehouse_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=p_name,
                sku=sku_val,
                quantity=item.quantity,
                reserved_quantity=item.reserved_quantity,
                aisle_location=item.aisle_location,
                updated_at=item.updated_at
            )
        )
    return results

