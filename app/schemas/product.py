from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.category import CategoryResponse
from app.schemas.brand import BrandResponse
from app.schemas.variant import VariantResponse
from app.schemas.media import ProductMediaResponse


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Decimal = Field(..., ge=Decimal("0.00"), description="Base selling price")
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    compare_at_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    base_sku: str = Field(..., min_length=2, max_length=100, description="Unique base SKU")
    currency: str = Field(default="USD", max_length=10)
    category_id: Optional[int] = Field(None, description="Primary category ID")
    brand_id: Optional[int] = Field(None, description="Brand ID")
    status: str = Field(default="ACTIVE", description="ACTIVE, INACTIVE, DRAFT, ARCHIVED")
    is_featured: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    cost_price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    base_sku: Optional[str] = Field(None, min_length=2, max_length=100)
    currency: Optional[str] = None
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Decimal
    cost_price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    base_sku: str
    currency: str
    category_id: Optional[int] = None
    brand_id: Optional[int] = None
    status: str
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    category: Optional[CategoryResponse] = None
    brand: Optional[BrandResponse] = None
    variants: List[VariantResponse] = []
    media: List[ProductMediaResponse] = []
