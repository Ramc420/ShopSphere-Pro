from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150, description="Recipient full name")
    phone_number: str = Field(..., min_length=7, max_length=32, description="Contact phone")
    address_type: str = Field(default="SHIPPING", description="SHIPPING, BILLING, or BOTH")
    street_line1: str = Field(..., min_length=3, max_length=255, description="Street address line 1")
    street_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state_province: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    country: str = Field(default="United States", min_length=2, max_length=100)
    is_default: bool = False
    is_default_billing: bool = False

    @field_validator("address_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        upper = v.upper()
        if upper not in ["SHIPPING", "BILLING", "BOTH"]:
            raise ValueError("address_type must be SHIPPING, BILLING, or BOTH")
        return upper


class AddressUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    phone_number: Optional[str] = Field(None, min_length=7, max_length=32)
    address_type: Optional[str] = None
    street_line1: Optional[str] = Field(None, min_length=3, max_length=255)
    street_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state_province: Optional[str] = Field(None, min_length=2, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    is_default: Optional[bool] = None
    is_default_billing: Optional[bool] = None


class AddressResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone_number: str
    address_type: str
    street_line1: str
    street_line2: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str
    is_default: bool
    is_default_billing: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderAddressAssociationRequest(BaseModel):
    shipping_address_id: int
    billing_address_id: int
    total_amount: Decimal = Field(default=Decimal("99.99"), ge=Decimal("0.00"))


class MockOrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    shipping_address_id: Optional[int]
    billing_address_id: Optional[int]
    status: str
    total_amount: Decimal
    shipping_address_snapshot: Optional[str]
    billing_address_snapshot: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
