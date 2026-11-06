import hashlib
import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.core.audit import log_user_activity
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.core.permissions import UserRole
from app.database import get_db
from app.models.media import ProductMedia
from app.models.product import Product
from app.models.user import User
from app.models.variant import ProductVariant
from app.schemas.common import MessageResponse
from app.schemas.media import MediaMetadataUpdate, ProductMediaResponse

router = APIRouter(prefix="/media", tags=["Module 10: Product Images and Documents"])


def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


@router.post("/upload", response_model=ProductMediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_media(
    request: Request,
    file: UploadFile = File(...),
    product_id: Optional[int] = Form(None),
    variant_id: Optional[int] = Form(None),
    file_type: str = Form("IMAGE", description="IMAGE, DOCUMENT, MANUAL, SPEC_SHEET"),
    is_primary: bool = Form(False),
    display_order: int = Form(0),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Upload and validate product images and documents (Module 10).
    - Validates file MIME types against whitelist.
    - Enforces maximum file size limit.
    - Computes SHA256 checksum and extracts image resolution metadata.
    - Associates file with product and optional variant.
    """
    # 1. Validate Product association if provided
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found")

    # 2. Validate Variant association if provided
    if variant_id:
        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Variant {variant_id} not found")

    # 3. Validate MIME type
    content_type = file.content_type or "application/octet-stream"
    file_type_upper = file_type.upper()
    
    all_allowed = settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_DOCUMENT_TYPES
    if content_type not in all_allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{content_type}'. Allowed types: {', '.join(all_allowed)}"
        )

    # 4. Prepare storage directory
    save_dir = os.path.join(settings.UPLOAD_DIR, "products", str(product_id or "general"))
    os.makedirs(save_dir, exist_ok=True)

    # Secure unique file name
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    dest_path = os.path.join(save_dir, unique_filename)

    # 5. Save and enforce file size
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    bytes_written = 0
    with open(dest_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            bytes_written += len(chunk)
            if bytes_written > max_bytes:
                buffer.close()
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
                )
            buffer.write(chunk)

    # 6. Extract image dimensions using Pillow if image
    img_width = None
    img_height = None
    if content_type in settings.ALLOWED_IMAGE_TYPES:
        try:
            with Image.open(dest_path) as img:
                img_width, img_height = img.size
                img.verify()  # Verify integrity
        except Exception as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Corrupt or invalid image file: {str(e)}"
            )

    # 7. Compute checksum
    checksum = compute_sha256(dest_path)

    # 8. Unset previous primary if this is primary
    if is_primary and product_id:
        existing_primaries = db.query(ProductMedia).filter(
            ProductMedia.product_id == product_id,
            ProductMedia.is_primary == True
        ).all()
        for p in existing_primaries:
            p.is_primary = False

    # 9. Create DB record
    file_url = f"/api/v1/media/files/{os.path.basename(dest_path)}"
    
    media_record = ProductMedia(
        product_id=product_id,
        variant_id=variant_id,
        original_filename=file.filename or "unknown",
        storage_path=dest_path,
        file_url=file_url,
        file_size_bytes=bytes_written,
        mime_type=content_type,
        file_type=file_type_upper,
        image_width=img_width,
        image_height=img_height,
        checksum_sha256=checksum,
        is_primary=is_primary,
        display_order=display_order,
        uploaded_by_user_id=current_user.id
    )
    db.add(media_record)
    db.commit()
    db.refresh(media_record)

    log_user_activity(
        db,
        action="MEDIA_UPLOADED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={
            "media_id": media_record.id,
            "filename": media_record.original_filename,
            "size_bytes": bytes_written,
            "mime_type": content_type
        }
    )

    return media_record


@router.get("/{media_id}", response_model=ProductMediaResponse)
def get_media_metadata(
    media_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored file metadata.
    """
    media = db.query(ProductMedia).filter(ProductMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")
    return media


@router.get("/{media_id}/download")
def download_media_file(
    media_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve and download authorized files.
    """
    media = db.query(ProductMedia).filter(ProductMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")

    if not os.path.exists(media.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical file missing from storage")

    return FileResponse(
        path=media.storage_path,
        media_type=media.mime_type,
        filename=media.original_filename
    )


@router.get("/files/{filename}")
def serve_media_by_filename(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Direct endpoint to view or serve authorized file by filename.
    """
    media = db.query(ProductMedia).filter(ProductMedia.storage_path.like(f"%{filename}")).first()
    if not media or not os.path.exists(media.storage_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(
        path=media.storage_path,
        media_type=media.mime_type
    )


@router.get("/product/{product_id}", response_model=List[ProductMediaResponse])
def get_media_for_product(
    product_id: int,
    file_type: Optional[str] = Query(None, description="IMAGE, DOCUMENT, MANUAL, SPEC_SHEET"),
    db: Session = Depends(get_db)
):
    """
    Retrieve all media files and documents associated with a product.
    """
    stmt = db.query(ProductMedia).filter(ProductMedia.product_id == product_id)
    if file_type:
        stmt = stmt.filter(ProductMedia.file_type == file_type.upper())
    return stmt.order_by(ProductMedia.is_primary.desc(), ProductMedia.display_order.asc()).all()


@router.put("/{media_id}/metadata", response_model=ProductMediaResponse)
def update_media_metadata(
    media_id: int,
    payload: MediaMetadataUpdate,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.EMPLOYEE.value)),
    db: Session = Depends(get_db)
):
    """
    Update media metadata (primary flag, display order, variant association).
    """
    media = db.query(ProductMedia).filter(ProductMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")

    if payload.is_primary is True and media.product_id:
        existing_primaries = db.query(ProductMedia).filter(
            ProductMedia.product_id == media.product_id,
            ProductMedia.is_primary == True,
            ProductMedia.id != media.id
        ).all()
        for p in existing_primaries:
            p.is_primary = False
        media.is_primary = True

    if payload.display_order is not None:
        media.display_order = payload.display_order

    if payload.variant_id is not None:
        variant = db.query(ProductVariant).filter(ProductVariant.id == payload.variant_id).first()
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found")
        media.variant_id = payload.variant_id

    db.commit()
    db.refresh(media)

    log_user_activity(
        db,
        action="MEDIA_METADATA_UPDATED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"media_id": media.id}
    )

    return media


@router.delete("/{media_id}", response_model=MessageResponse)
def delete_media_file(
    media_id: int,
    request: Request,
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
):
    """
    Remove authorized file: deletes physical file on disk and removes metadata from database.
    """
    media = db.query(ProductMedia).filter(ProductMedia.id == media_id).first()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")

    # Delete physical file from disk
    if os.path.exists(media.storage_path):
        try:
            os.remove(media.storage_path)
        except Exception:
            pass

    filename = media.original_filename
    db.delete(media)
    db.commit()

    log_user_activity(
        db,
        action="MEDIA_DELETED",
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        details={"media_id": media_id, "filename": filename}
    )

    return MessageResponse(
        success=True,
        message=f"Media file '{filename}' (ID: {media_id}) successfully removed."
    )
