from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.category import Category
from app.models.tax import TaxHistory, TaxRate
from app.models.user import User
from app.schemas.tax import (
    TaxCalculationRequest,
    TaxCalculationResponse,
    TaxHistoryResponse,
    TaxRateCreate,
    TaxRateResponse,
    TaxRateUpdate,
)

router = APIRouter(prefix="/taxes", tags=["Module 22: Tax Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("", response_model=TaxRateResponse, status_code=status.HTTP_201_CREATED)
def create_tax_rate(
    payload: TaxRateCreate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Configure a new applicable tax rate for a country, state/province, or product category.
    """
    if payload.category_id:
        c = db.query(Category).filter(Category.id == payload.category_id).first()
        if not c:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    tax = TaxRate(
        name=payload.name.strip(),
        country=payload.country.strip().upper(),
        state_province=payload.state_province.strip().upper(),
        postal_code=payload.postal_code.strip() if payload.postal_code else None,
        rate_percentage=payload.rate_percentage,
        category_id=payload.category_id,
        is_active=payload.is_active
    )
    db.add(tax)
    db.commit()
    db.refresh(tax)

    log_user_activity(
        db,
        action="TAX_RATE_CREATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"tax_id": tax.id, "rate": float(tax.rate_percentage)}
    )

    return tax


@router.get("", response_model=List[TaxRateResponse])
def get_tax_rates(
    country: Optional[str] = None,
    state_province: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    List configured tax rates.
    """
    stmt = db.query(TaxRate)
    if country:
        stmt = stmt.filter(TaxRate.country == country.upper())
    if state_province:
        stmt = stmt.filter(TaxRate.state_province == state_province.upper())
    return stmt.order_by(TaxRate.id.asc()).all()


@router.put("/{tax_id}", response_model=TaxRateResponse)
def update_tax_rate(
    tax_id: int,
    payload: TaxRateUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Update tax rate and record the modification in TaxHistory.
    """
    tax = db.query(TaxRate).filter(TaxRate.id == tax_id).first()
    if not tax:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax rate not found")

    old_rate = float(tax.rate_percentage)

    if payload.rate_percentage is not None and payload.rate_percentage != old_rate:
        # Record change history
        hist = TaxHistory(
            tax_rate_id=tax.id,
            old_rate=old_rate,
            new_rate=payload.rate_percentage,
            change_reason=payload.change_reason or "Statutory tax rate adjustment",
            changed_by_user_id=current_user.id
        )
        db.add(hist)
        tax.rate_percentage = payload.rate_percentage

    if payload.name is not None:
        tax.name = payload.name.strip()
    if payload.is_active is not None:
        tax.is_active = payload.is_active

    tax.updated_at = utc_now()
    db.commit()
    db.refresh(tax)

    return tax


@router.get("/history", response_model=List[TaxHistoryResponse])
def get_tax_history(
    tax_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit history of tax rate modifications.
    """
    stmt = db.query(TaxHistory)
    if tax_id:
        stmt = stmt.filter(TaxHistory.tax_rate_id == tax_id)
    return stmt.order_by(TaxHistory.created_at.desc()).all()


@router.post("/calculate", response_model=TaxCalculationResponse)
def calculate_tax(
    payload: TaxCalculationRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate applicable tax based on order subtotal and customer destination region.
    """
    country_clean = payload.country.strip().upper()
    state_clean = payload.state_province.strip().upper()

    # Look for exact state match or wildcard '*'
    rule = db.query(TaxRate).filter(
        TaxRate.is_active == True,
        TaxRate.country == country_clean,
        TaxRate.state_province == state_clean
    ).first()

    if not rule:
        rule = db.query(TaxRate).filter(
            TaxRate.is_active == True,
            TaxRate.country == country_clean,
            TaxRate.state_province == "*"
        ).first()

    rate = float(rule.rate_percentage) if rule else 8.0  # Default fallback 8%
    rule_name = rule.name if rule else "Standard National Tax"
    tax_amt = round(payload.amount * (rate / 100.0), 2)

    return TaxCalculationResponse(
        rate_percentage=rate,
        taxable_amount=payload.amount,
        tax_amount=tax_amt,
        rule_name=rule_name
    )

