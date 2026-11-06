from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    slug: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    parent_id: Optional[int] = Field(None, description="Parent category ID for subcategories")
    image_url: Optional[str] = Field(None, max_length=500)
    display_order: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    slug: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryTreeNode(CategoryResponse):
    children: List[CategoryTreeNode] = []


class CategoryBreadcrumb(BaseModel):
    id: int
    name: str
    slug: str
