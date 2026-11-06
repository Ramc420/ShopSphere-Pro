from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ProductReview(Base):
    """
    Module 38: Product Reviews and Ratings
    Verified purchaser reviews, 1-5 star ratings, comments,
    moderation approval, and duplicate prevention.
    """
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5
    title = Column(String(150), nullable=True)
    comment = Column(Text, nullable=False)
    is_verified_purchase = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="PENDING", index=True, nullable=False)  # PENDING, APPROVED, REJECTED
    moderation_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "user_id", name="uq_product_user_review"),
    )

    product = relationship("Product")
    user = relationship("User")
    order = relationship("Order")


class ProductQuestion(Base):
    """
    Module 39: Product Questions and Answers
    Customer product inquiries, moderation status, and answer threads.
    """
    __tablename__ = "product_questions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", index=True, nullable=False)  # PENDING, APPROVED, REJECTED

    created_at = Column(DateTime, default=utc_now, nullable=False)

    product = relationship("Product")
    user = relationship("User")
    answers = relationship("ProductAnswer", back_populates="question", cascade="all, delete-orphan")


class ProductAnswer(Base):
    """
    Module 39: Product Answers
    Staff and vendor responses to customer questions.
    """
    __tablename__ = "product_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("product_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = Column(Text, nullable=False)
    is_staff_answer = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    question = relationship("ProductQuestion", back_populates="answers")
    user = relationship("User")

