from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr


class SupplierCreate(BaseModel):
    supplier_code: str
    company_name: str
    supplier_type: Optional[str] = "SUPPLIER"
    contact_name: str
    email: EmailStr
    phone: str
    tax_id: Optional[str] = None
    business_registration_number: Optional[str] = None
    address_line: str
    city: str
    state: str
    country: Optional[str] = "USA"
    postal_code: str
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    notes: Optional[str] = None


class SupplierApprovalUpdate(BaseModel):
    status: str  # APPROVED, REJECTED, SUSPENDED
    notes: Optional[str] = None


class SupplierHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    changed_by_user_id: Optional[int] = None
    action: str
    from_status: Optional[str] = None
    to_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class ProductSupplierCreate(BaseModel):
    product_id: int
    supplier_sku: Optional[str] = None
    negotiated_cost: Decimal
    lead_time_days: Optional[int] = 7
    is_primary: Optional[bool] = False


class ProductSupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    product_id: int
    supplier_sku: Optional[str] = None
    negotiated_cost: Decimal
    lead_time_days: int
    is_primary: bool
    created_at: datetime


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_code: str
    company_name: str
    supplier_type: str
    contact_name: str
    email: str
    phone: str
    tax_id: Optional[str] = None
    business_registration_number: Optional[str] = None
    address_line: str
    city: str
    state: str
    country: str
    postal_code: str
    status: str
    rating: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

