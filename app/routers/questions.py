from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.product_interaction import ProductQuestion, ProductAnswer
from app.schemas.product_qa import (
    ProductQuestionCreate, ProductQuestionModeration, ProductAnswerCreate,
    ProductAnswerResponse, ProductQuestionResponse
)
from app.core.dependencies import get_current_user, require_permissions
from app.core.permissions import Permission

router = APIRouter(prefix="/questions", tags=["Module 39: Product Questions and Answers"])


@router.post("/products/{product_id}", response_model=ProductQuestionResponse, status_code=status.HTTP_201_CREATED)
def submit_product_question(
    product_id: int,
    payload: ProductQuestionCreate,
    current_user: User = Depends(require_permissions(Permission.QUESTIONS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Module 39: Customers submit product-related inquiries.
    """
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    q = ProductQuestion(
        product_id=product_id,
        user_id=current_user.id,
        question_text=payload.question_text.strip(),
        status="APPROVED"
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.get("/products/{product_id}", response_model=List[ProductQuestionResponse])
def get_product_questions(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve public product Q&A discussions.
    """
    questions = db.query(ProductQuestion).filter(
        ProductQuestion.product_id == product_id,
        ProductQuestion.status == "APPROVED"
    ).order_by(ProductQuestion.created_at.desc()).all()
    return questions


@router.post("/{question_id}/answers", response_model=ProductAnswerResponse, status_code=status.HTTP_201_CREATED)
def answer_product_question(
    question_id: int,
    payload: ProductAnswerCreate,
    current_user: User = Depends(require_permissions(Permission.QUESTIONS_WRITE.value)),
    db: Session = Depends(get_db)
):
    """
    Authorized staff, vendors, or customers reply to product questions.
    """
    q = db.query(ProductQuestion).filter(ProductQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    is_staff = current_user.role in ["SUPER_ADMIN", "ADMIN", "EMPLOYEE"]
    ans = ProductAnswer(
        question_id=question_id,
        user_id=current_user.id,
        answer_text=payload.answer_text.strip(),
        is_staff_answer=is_staff
    )
    db.add(ans)
    q.status = "APPROVED"
    db.commit()
    db.refresh(ans)
    return ans


@router.patch("/{question_id}/moderation", response_model=ProductQuestionResponse)
def moderate_question(
    question_id: int,
    payload: ProductQuestionModeration,
    current_user: User = Depends(require_permissions(Permission.QUESTIONS_MODERATE.value)),
    db: Session = Depends(get_db)
):
    """
    Moderate question status (APPROVED, REJECTED) to manage inappropriate content.
    """
    q = db.query(ProductQuestion).filter(ProductQuestion.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    q.status = payload.status.upper()
    db.commit()
    db.refresh(q)
    return q

