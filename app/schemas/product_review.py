from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict, Field


class ProductReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = None
    comment: str
    order_id: Optional[int] = None


class ProductReviewModeration(BaseModel):
    status: str  # APPROVED, REJECTED
    moderation_notes: Optional[str] = None


class ProductReviewResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    order_id: Optional[int] = None
    rating: int
    title: Optional[str] = None
    comment: str
    is_verified_purchase: bool
    status: str
    moderation_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductRatingSummary(BaseModel):
    product_id: int
    average_rating: float
    total_reviews: int
    rating_distribution: Dict[str, int]

