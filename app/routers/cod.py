from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.cod import CODConfig, CODCollection
from app.schemas.cod import (
    CODConfigUpdate, CODConfigResponse, CODEligibilityCheck,
    CODEligibilityResponse, CODRecordCollection, CODCollectionResponse
)
from app.core.dependencies import require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/cod", tags=["Module 32: Cash on Delivery Management"])


def utc_now():
    return datetime.now(timezone.utc)


def get_or_create_cod_config(db: Session) -> CODConfig:
    cfg = db.query(CODConfig).first()
    if not cfg:
        cfg = CODConfig(
            is_enabled=True,
            min_order_amount=Decimal("10.00"),
            max_order_amount=Decimal("1500.00"),
            restricted_postal_codes=["99999", "00000", "REMOTE-1"],
            extra_fee=Decimal("5.00")
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.get("/config", response_model=CODConfigResponse)
def get_cod_configuration(
    db: Session = Depends(get_db)
):
    """
    Retrieve current Cash on Delivery rules and eligibility thresholds.
    """
    return get_or_create_cod_config(db)


@router.put("/config", response_model=CODConfigResponse)
def update_cod_configuration(
    payload: CODConfigUpdate,
    current_user: User = Depends(require_permissions(Permission.COD_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Configure Cash on Delivery eligibility rules, bounds, and fee surcharges (Admin only).
    """
    cfg = get_or_create_cod_config(db)
    cfg.is_enabled = payload.is_enabled
    cfg.min_order_amount = Decimal(str(payload.min_order_amount))
    cfg.max_order_amount = Decimal(str(payload.max_order_amount))
    cfg.restricted_postal_codes = payload.restricted_postal_codes
    cfg.extra_fee = Decimal(str(payload.extra_fee))
    cfg.updated_at = utc_now()
    db.commit()
    db.refresh(cfg)
    return cfg


@router.post("/validate-eligibility", response_model=CODEligibilityResponse)
def validate_cod_eligibility(
    payload: CODEligibilityCheck,
    db: Session = Depends(get_db)
):
    """
    Validate order and delivery restrictions to verify whether COD is permitted.
    """
    cfg = get_or_create_cod_config(db)
    if not cfg.is_enabled:
        return CODEligibilityResponse(is_eligible=False, reason="Cash on Delivery is currently disabled globally")

    amt = Decimal(str(payload.order_amount))
    if amt < cfg.min_order_amount:
        return CODEligibilityResponse(
            is_eligible=False,
            reason=f"Order amount ${float(amt):.2f} is below minimum COD threshold of ${float(cfg.min_order_amount):.2f}"
        )

    if amt > cfg.max_order_amount:
        return CODEligibilityResponse(
            is_eligible=False,
            reason=f"Order amount ${float(amt):.2f} exceeds maximum COD threshold of ${float(cfg.max_order_amount):.2f}"
        )

    if payload.postal_code and any(res.strip().lower() in payload.postal_code.lower() for res in cfg.restricted_postal_codes):
        return CODEligibilityResponse(
            is_eligible=False,
            reason=f"Delivery location postal code '{payload.postal_code}' is in a restricted COD zone"
        )

    return CODEligibilityResponse(is_eligible=True, extra_fee=float(cfg.extra_fee))


@router.post("/collections/{order_id}/collect", response_model=CODCollectionResponse)
def record_cod_collection(
    order_id: int,
    payload: CODRecordCollection,
    current_user: User = Depends(require_permissions(Permission.COD_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Record courier cash collection and reconcile with order payment status.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    collection = db.query(CODCollection).filter(CODCollection.order_id == order_id).first()
    if not collection:
        collection = CODCollection(
            order_id=order.id,
            expected_amount=order.total_amount,
            status="PENDING"
        )
        db.add(collection)

    coll_amount = Decimal(str(payload.collected_amount))
    collection.collected_amount = coll_amount
    collection.collected_by = payload.collected_by or current_user.email
    collection.collected_at = utc_now()
    collection.notes = payload.notes

    if coll_amount >= Decimal(str(order.total_amount)):
        collection.status = "COLLECTED"
        collection.reconciled_at = utc_now()
        order.payment_status = "PAID"
    else:
        collection.status = "PARTIALLY_COLLECTED"

    db.commit()
    db.refresh(collection)
    return collection


@router.get("/collections", response_model=List[CODCollectionResponse])
def list_cod_collections(
    current_user: User = Depends(require_permissions(Permission.COD_MANAGE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve COD collections for financial reconciliation.
    """
    collections = db.query(CODCollection).order_by(CODCollection.created_at.desc()).all()
    return collections

