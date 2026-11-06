from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None


class PaginationMeta(BaseModel):
    total_items: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    meta: PaginationMeta

