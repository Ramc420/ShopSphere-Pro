from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class SupplierInvoice(Base):
    __tablename__ = "supplier_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_date = Column(DateTime(timezone=True), default=utc_now)
    due_date = Column(DateTime(timezone=True), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(30), default="UNPAID", index=True)  # UNPAID, PARTIALLY_PAID, PAID, VOID
    amount_paid = Column(Numeric(12, 2), default=0.00)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("invoice_number", "supplier_id", name="uq_invoice_supplier"),
    )

    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder")

