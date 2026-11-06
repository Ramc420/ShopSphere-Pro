from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class SupplierInvoiceCreate(BaseModel):
    invoice_number: str
    supplier_id: int
    purchase_order_id: int
    due_date: datetime
    subtotal: Decimal
    tax_amount: Optional[Decimal] = Decimal("0.00")
    total_amount: Decimal
    notes: Optional[str] = None


class SupplierInvoicePaymentUpdate(BaseModel):
    payment_status: str  # UNPAID, PARTIALLY_PAID, PAID, VOID
    amount_paid: Decimal
    notes: Optional[str] = None


class SupplierInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    supplier_id: int
    purchase_order_id: int
    invoice_date: datetime
    due_date: datetime
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_status: str
    amount_paid: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

