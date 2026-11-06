from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class VariantCreate(BaseModel):
    sku: str = Field(..., min_length=2, max_length=100, description="Unique SKU code for variant")
    title: str = Field(..., min_length=2, max_length=150, description="e.g. 'Size XL / Navy Blue'")
    price: Decimal = Field(..., ge=Decimal("0.00"), description="Variant price")
    compare_at_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="e.g. {'size': 'XL', 'color': 'Navy'}")
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    status: str = Field(default="ACTIVE", description="ACTIVE, INACTIVE, DISCONTINUED")


class VariantUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=2, max_length=100)
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    attributes: Optional[Dict[str, Any]] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None


class VariantStockAdjust(BaseModel):
    adjustment: int = Field(..., description="Positive to add stock, negative to reduce")
    reason: Optional[str] = None


class VariantResponse(BaseModel):
    id: int
    product_id: int
    sku: str
    title: str
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    attributes: Optional[Dict[str, Any]] = None
    stock_quantity: int
    reserved_quantity: int
    low_stock_threshold: int
    availability_status: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
