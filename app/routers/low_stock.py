from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.inventory import InventoryItem
from app.models.low_stock import LowStockThreshold, RestockAlert, StockThresholdChangeHistory
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.models.warehouse import Warehouse, WarehouseInventory
from app.schemas.low_stock import (
    LowStockReportItem,
    RestockAlertResponse,
    ThresholdConfigure,
    ThresholdHistoryResponse,
    ThresholdResponse,
)

router = APIRouter(prefix="/low-stock", tags=["Module 16: Low-Stock Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("/thresholds", response_model=ThresholdResponse)
def configure_stock_threshold(
    payload: ThresholdConfigure,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Configure minimum stock threshold for a product or variant.
    Tracks threshold change history in StockThresholdChangeHistory.
    """
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if payload.variant_id:
        variant = db.query(ProductVariant).filter(
            ProductVariant.id == payload.variant_id,
            ProductVariant.product_id == payload.product_id
        ).first()
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")

    threshold_record = db.query(LowStockThreshold).filter(
        LowStockThreshold.product_id == payload.product_id,
        LowStockThreshold.variant_id == payload.variant_id,
        LowStockThreshold.warehouse_id == payload.warehouse_id
    ).first()

    old_val = threshold_record.threshold if threshold_record else 10

    if threshold_record:
        threshold_record.threshold = payload.threshold
        threshold_record.reorder_quantity = payload.reorder_quantity
    else:
        threshold_record = LowStockThreshold(
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            warehouse_id=payload.warehouse_id,
            threshold=payload.threshold,
            reorder_quantity=payload.reorder_quantity
        )
        db.add(threshold_record)

    # Sync low_stock_threshold on variant or inventory item
    if payload.variant_id:
        v = db.query(ProductVariant).filter(ProductVariant.id == payload.variant_id).first()
        if v:
            v.low_stock_threshold = payload.threshold
    inv_item = db.query(InventoryItem).filter(
        InventoryItem.product_id == payload.product_id,
        InventoryItem.variant_id == payload.variant_id
    ).first()
    if inv_item:
        inv_item.low_stock_threshold = payload.threshold

    # Record threshold change history
    history = StockThresholdChangeHistory(
        product_id=payload.product_id,
        variant_id=payload.variant_id,
        old_threshold=old_val,
        new_threshold=payload.threshold,
        change_reason=payload.change_reason or "Minimum threshold adjustment",
        changed_by_user_id=current_user.id
    )
    db.add(history)
    db.commit()
    db.refresh(threshold_record)

    log_user_activity(
        db,
        action="STOCK_THRESHOLD_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"product_id": payload.product_id, "old": old_val, "new": payload.threshold}
    )

    return threshold_record


@router.get("/thresholds", response_model=List[ThresholdResponse])
def get_thresholds(
    product_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    List configured minimum stock thresholds.
    """
    stmt = db.query(LowStockThreshold)
    if product_id:
        stmt = stmt.filter(LowStockThreshold.product_id == product_id)
    return stmt.all()


@router.get("/thresholds/history", response_model=List[ThresholdHistoryResponse])
def get_threshold_change_history(
    product_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit history of stock threshold modifications.
    """
    stmt = db.query(StockThresholdChangeHistory)
    if product_id:
        stmt = stmt.filter(StockThresholdChangeHistory.product_id == product_id)
    return stmt.order_by(StockThresholdChangeHistory.created_at.desc()).all()


@router.post("/alerts/generate", response_model=List[RestockAlertResponse])
def generate_restock_alerts(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Scans live inventory levels across products and variants,
    detects items below their threshold, and generates restock alerts.
    """
    items = db.query(InventoryItem).all()
    created_alerts = []

    for item in items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if not prod:
            continue

        threshold_val = item.low_stock_threshold or 10
        if item.available_quantity <= threshold_val:
            # Determine severity
            if item.available_quantity <= 0:
                severity = "OUT_OF_STOCK"
            elif item.available_quantity <= max(1, threshold_val // 2):
                severity = "CRITICAL"
            else:
                severity = "LOW"

            # Check if active alert already exists
            existing = db.query(RestockAlert).filter(
                RestockAlert.product_id == item.product_id,
                RestockAlert.variant_id == item.variant_id,
                RestockAlert.is_resolved == False
            ).first()

            var = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first() if item.variant_id else None
            sku_val = var.sku if var else prod.base_sku

            if existing:
                existing.current_stock = item.available_quantity
                existing.severity = severity
                alert = existing
            else:
                alert = RestockAlert(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    current_stock=item.available_quantity,
                    threshold=threshold_val,
                    severity=severity,
                    is_resolved=False,
                    notes=f"Current available stock ({item.available_quantity}) is at or below threshold ({threshold_val})."
                )
                db.add(alert)
                db.flush()

            created_alerts.append(
                RestockAlertResponse(
                    id=alert.id,
                    product_id=alert.product_id,
                    variant_id=alert.variant_id,
                    warehouse_id=alert.warehouse_id,
                    current_stock=alert.current_stock,
                    threshold=alert.threshold,
                    severity=alert.severity,
                    is_resolved=alert.is_resolved,
                    notes=alert.notes,
                    created_at=alert.created_at,
                    resolved_at=alert.resolved_at,
                    product_name=prod.name,
                    sku=sku_val
                )
            )

    db.commit()
    return created_alerts


@router.get("/alerts", response_model=List[RestockAlertResponse])
def get_restock_alerts(
    is_resolved: Optional[bool] = Query(False, description="Filter resolved alerts"),
    severity: Optional[str] = Query(None, description="LOW, CRITICAL, OUT_OF_STOCK"),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve active or past restocking alerts.
    """
    stmt = db.query(RestockAlert)
    if is_resolved is not None:
        stmt = stmt.filter(RestockAlert.is_resolved == is_resolved)
    if severity:
        stmt = stmt.filter(RestockAlert.severity == severity.upper())

    alerts = stmt.order_by(RestockAlert.created_at.desc()).all()
    results = []
    for a in alerts:
        prod = db.query(Product).filter(Product.id == a.product_id).first()
        var = db.query(ProductVariant).filter(ProductVariant.id == a.variant_id).first() if a.variant_id else None
        results.append(
            RestockAlertResponse(
                id=a.id,
                product_id=a.product_id,
                variant_id=a.variant_id,
                warehouse_id=a.warehouse_id,
                current_stock=a.current_stock,
                threshold=a.threshold,
                severity=a.severity,
                is_resolved=a.is_resolved,
                notes=a.notes,
                created_at=a.created_at,
                resolved_at=a.resolved_at,
                product_name=prod.name if prod else "Unknown",
                sku=var.sku if var else (prod.base_sku if prod else "N/A")
            )
        )
    return results


@router.post("/alerts/{alert_id}/resolve", response_model=RestockAlertResponse)
def resolve_restock_alert(
    alert_id: int,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Mark a restocking alert as resolved once stock has been replenished.
    """
    alert = db.query(RestockAlert).filter(RestockAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    alert.is_resolved = True
    alert.resolved_at = utc_now()
    db.commit()
    db.refresh(alert)

    prod = db.query(Product).filter(Product.id == alert.product_id).first()
    var = db.query(ProductVariant).filter(ProductVariant.id == alert.variant_id).first() if alert.variant_id else None

    return RestockAlertResponse(
        id=alert.id,
        product_id=alert.product_id,
        variant_id=alert.variant_id,
        warehouse_id=alert.warehouse_id,
        current_stock=alert.current_stock,
        threshold=alert.threshold,
        severity=alert.severity,
        is_resolved=alert.is_resolved,
        notes=alert.notes,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at,
        product_name=prod.name if prod else "Unknown",
        sku=var.sku if var else (prod.base_sku if prod else "N/A")
    )


@router.get("/report", response_model=List[LowStockReportItem])
def get_low_stock_report(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive low-stock and replenishment report across the entire catalog.
    """
    inv_items = db.query(InventoryItem).all()
    report = []

    for item in inv_items:
        threshold = item.low_stock_threshold or 10
        if item.available_quantity <= threshold:
            prod = db.query(Product).filter(Product.id == item.product_id).first()
            if not prod:
                continue
            var = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first() if item.variant_id else None

            shortage = max(0, threshold - item.available_quantity)
            if item.available_quantity <= 0:
                severity = "OUT_OF_STOCK"
            elif item.available_quantity <= threshold // 2:
                severity = "CRITICAL"
            else:
                severity = "LOW"

            reorder_qty = 50
            thresh_conf = db.query(LowStockThreshold).filter(
                LowStockThreshold.product_id == item.product_id,
                LowStockThreshold.variant_id == item.variant_id
            ).first()
            if thresh_conf:
                reorder_qty = thresh_conf.reorder_quantity

            report.append(
                LowStockReportItem(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    product_name=prod.name,
                    sku=var.sku if var else prod.base_sku,
                    current_stock=item.available_quantity,
                    threshold=threshold,
                    shortage=shortage,
                    severity=severity,
                    reorder_recommended=reorder_qty
                )
            )

    return report

