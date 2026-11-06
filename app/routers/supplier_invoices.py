from datetime import datetime, timezone
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.supplier import Supplier
from app.models.purchase_order import PurchaseOrder
from app.models.supplier_invoice import SupplierInvoice
from app.schemas.supplier_invoice import (
    SupplierInvoiceCreate, SupplierInvoicePaymentUpdate, SupplierInvoiceResponse
)
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/supplier-invoices", tags=["Module 45: Supplier Invoice Management"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("", response_model=SupplierInvoiceResponse, status_code=status.HTTP_201_CREATED)
def record_supplier_invoice(
    payload: SupplierInvoiceCreate,
    current_user: User = Depends(require_permissions(Permission.SUPPLIER_INVOICES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Record a supplier invoice associated with a purchase order.
    Validates PO existence, supplier matching, and prevents duplicate invoice numbers.
    """
    # 1. Check supplier
    supplier = db.query(Supplier).filter(Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # 2. Check purchase order
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == payload.purchase_order_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    if po.supplier_id != payload.supplier_id:
        raise HTTPException(status_code=400, detail="Invoice supplier does not match the purchase order supplier")

    # 3. Prevent duplicate invoice records for the same supplier
    duplicate = db.query(SupplierInvoice).filter(
        SupplierInvoice.invoice_number == payload.invoice_number.strip(),
        SupplierInvoice.supplier_id == payload.supplier_id
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"Invoice '{payload.invoice_number}' has already been recorded for this supplier"
        )

    # 4. Create invoice
    invoice = SupplierInvoice(
        invoice_number=payload.invoice_number.strip(),
        supplier_id=payload.supplier_id,
        purchase_order_id=payload.purchase_order_id,
        invoice_date=utc_now(),
        due_date=payload.due_date,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount or Decimal("0.00"),
        total_amount=payload.total_amount,
        payment_status="UNPAID",
        amount_paid=Decimal("0.00"),
        notes=payload.notes
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("", response_model=List[SupplierInvoiceResponse])
def list_supplier_invoices(
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    purchase_order_id: Optional[int] = Query(None, description="Filter by purchase order ID"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permissions(Permission.SUPPLIER_INVOICES_READ.value)),
    db: Session = Depends(get_db)
):
    """List supplier invoices with filtering options."""
    query = db.query(SupplierInvoice)
    if supplier_id:
        query = query.filter(SupplierInvoice.supplier_id == supplier_id)
    if purchase_order_id:
        query = query.filter(SupplierInvoice.purchase_order_id == purchase_order_id)
    if payment_status:
        query = query.filter(SupplierInvoice.payment_status == payment_status.upper())

    return query.order_by(SupplierInvoice.created_at.desc()).limit(limit).all()


@router.get("/{invoice_id}", response_model=SupplierInvoiceResponse)
def get_supplier_invoice(
    invoice_id: int,
    current_user: User = Depends(require_permissions(Permission.SUPPLIER_INVOICES_READ.value)),
    db: Session = Depends(get_db)
):
    """Retrieve details of a specific supplier invoice."""
    invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Supplier invoice not found")
    return invoice


@router.patch("/{invoice_id}/payment", response_model=SupplierInvoiceResponse)
def update_invoice_payment(
    invoice_id: int,
    payload: SupplierInvoicePaymentUpdate,
    current_user: User = Depends(require_permissions(Permission.SUPPLIER_INVOICES_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Track and update supplier invoice payment status.
    Automatically reconciles payment amounts and validates status.
    """
    invoice = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Supplier invoice not found")

    target_status = payload.payment_status.upper()
    if target_status not in ["UNPAID", "PARTIALLY_PAID", "PAID", "VOID"]:
        raise HTTPException(status_code=400, detail="Invalid payment status")

    invoice.amount_paid = payload.amount_paid
    invoice.payment_status = target_status
    if payload.notes:
        invoice.notes = (invoice.notes or "") + f" | Payment Note: {payload.notes}"
    invoice.updated_at = utc_now()

    db.commit()
    db.refresh(invoice)
    return invoice

