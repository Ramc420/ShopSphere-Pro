from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class BrandCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    code: Optional[str] = Field(None, max_length=100, description="Unique identifier or slug")
    description: Optional[str] = None
    website_url: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    status: str = Field(default="ACTIVE", description="ACTIVE or INACTIVE")


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    status: Optional[str] = None


class BrandResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    status: str
    products_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
