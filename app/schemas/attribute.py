from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AttributeOptionCreate(BaseModel):
    value: str = Field(..., min_length=1, max_length=150)
    display_order: int = 0


class AttributeOptionResponse(BaseModel):
    id: int
    attribute_id: int
    value: str
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class AttributeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: Optional[str] = Field(None, max_length=100)
    data_type: str = Field(default="TEXT", description="TEXT, NUMBER, SELECT, BOOLEAN")
    is_required: bool = False
    is_filterable: bool = True
    options: Optional[List[str]] = Field(default_factory=list, description="For SELECT data type")


class AttributeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, max_length=100)
    is_required: Optional[bool] = None
    is_filterable: Optional[bool] = None


class AttributeResponse(BaseModel):
    id: int
    name: str
    code: str
    data_type: str
    is_required: bool
    is_filterable: bool
    options: List[AttributeOptionResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryAttributeAssign(BaseModel):
    category_id: int
    attribute_id: int
    is_required: bool = False


class CategoryAttributeResponse(BaseModel):
    id: int
    category_id: int
    attribute_id: int
    is_required: bool
    attribute: Optional[AttributeResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ProductAttributeAssign(BaseModel):
    attribute_id: int
    value: str = Field(..., min_length=1, max_length=255)


class ProductAttributeValueResponse(BaseModel):
    id: int
    product_id: int
    attribute_id: int
    attribute_code: Optional[str] = None
    attribute_name: Optional[str] = None
    value: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

