from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.product_interaction import ProductReview
from app.schemas.product_review import (
    ProductReviewCreate, ProductReviewModeration, ProductReviewResponse, ProductRatingSummary
)
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/reviews", tags=["Module 38: Product Reviews and Ratings"])


@router.post("/products/{product_id}", response_model=ProductReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_product_review(
    product_id: int,
    payload: ProductReviewCreate,
    current_user: User = Depends(require_permissions(Permission.REVIEWS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 38: Allow verified purchasers or registered customers to review products.
    Enforces duplicate review prevention (one review per customer per product).
    Automatically flags as verified purchase if user completed an order with this product.
    """
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Duplicate check
    existing = db.query(ProductReview).filter(
        ProductReview.product_id == product_id,
        ProductReview.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted a review for this product"
        )

    # Check verified purchase
    verified_order = db.query(Order).join(OrderItem).filter(
        Order.user_id == current_user.id,
        Order.status == "DELIVERED",
        OrderItem.product_id == product_id
    ).first()

    is_verified = verified_order is not None
    order_id = payload.order_id or (verified_order.id if verified_order else None)

    review = ProductReview(
        product_id=product_id,
        user_id=current_user.id,
        order_id=order_id,
        rating=payload.rating,
        title=payload.title,
        comment=payload.comment,
        is_verified_purchase=is_verified,
        status="APPROVED"  # Auto-approve by default, or PENDING if flagged
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/products/{product_id}", response_model=List[ProductReviewResponse])
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve approved customer reviews for a given product.
    """
    reviews = db.query(ProductReview).filter(
        ProductReview.product_id == product_id,
        ProductReview.status == "APPROVED"
    ).order_by(ProductReview.created_at.desc()).all()
    return reviews


@router.get("/products/{product_id}/summary", response_model=ProductRatingSummary)
def get_product_rating_summary(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Calculate average rating, review count, and star distribution for a product.
    """
    reviews = db.query(ProductReview).filter(
        ProductReview.product_id == product_id,
        ProductReview.status == "APPROVED"
    ).all()

    total = len(reviews)
    dist = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    for r in reviews:
        dist[str(r.rating)] = dist.get(str(r.rating), 0) + 1

    avg = sum(r.rating for r in reviews) / total if total > 0 else 0.0

    return ProductRatingSummary(
        product_id=product_id,
        average_rating=round(avg, 2),
        total_reviews=total,
        rating_distribution=dist
    )


@router.patch("/{review_id}/moderation", response_model=ProductReviewResponse)
def moderate_product_review(
    review_id: int,
    payload: ProductReviewModeration,
    current_user: User = Depends(require_permissions(Permission.REVIEWS_MODERATE.value)),
    db: Session = Depends(get_db)
):
    """
    Moderate or approve/reject reviews with administrative authority.
    """
    review = db.query(ProductReview).filter(ProductReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    review.status = payload.status.upper()
    if payload.moderation_notes:
        review.moderation_notes = payload.moderation_notes

    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete review (Super Admin, Admin, or Review author).
    """
    review = db.query(ProductReview).filter(ProductReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if current_user.role not in ["SUPER_ADMIN", "ADMIN"] and review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(review)
    db.commit()
    return None

