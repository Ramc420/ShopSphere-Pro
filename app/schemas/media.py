from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductMediaResponse(BaseModel):
    id: int
    product_id: Optional[int]
    variant_id: Optional[int]
    original_filename: str
    file_url: str
    file_size_bytes: int
    mime_type: str
    file_type: str
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    checksum_sha256: Optional[str] = None
    is_primary: bool
    display_order: int
    uploaded_by_user_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaMetadataUpdate(BaseModel):
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None
    variant_id: Optional[int] = None
