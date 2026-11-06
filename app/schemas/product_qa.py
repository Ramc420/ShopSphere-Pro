from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ProductQuestionCreate(BaseModel):
    question_text: str


class ProductQuestionModeration(BaseModel):
    status: str  # APPROVED, REJECTED


class ProductAnswerCreate(BaseModel):
    answer_text: str


class ProductAnswerResponse(BaseModel):
    id: int
    question_id: int
    user_id: int
    answer_text: str
    is_staff_answer: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductQuestionResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    question_text: str
    status: str
    answers: List[ProductAnswerResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

