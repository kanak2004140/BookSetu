"""Pydantic request/response models."""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from .models.marketplace import OrderStatus


class ORM(BaseModel):
    model_config = {"from_attributes": True}


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # bcrypt ignores bytes past 72


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(ORM):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Books ─────────────────────────────────────────────────────────────────────

class BookListResponse(ORM):
    id: int
    title: str
    author: str
    category: str
    selling_price: float
    cover_image_path: Optional[str]
    pdf_path: Optional[str]
    condition: str
    is_rentable: bool
    rent_price: Optional[float]
    seller_id: int


class BookResponse(BookListResponse):
    original_price: float
    description: Optional[str]
    bestseller: bool
    created_at: datetime
    updated_at: datetime


# ── Cart & orders ─────────────────────────────────────────────────────────────

class CartItemAdd(BaseModel):
    book_id: int
    quantity: int = Field(default=1, gt=0, le=100)


class CartItemResponse(ORM):
    id: int
    book_id: int
    quantity: int
    book: BookListResponse


class CartResponse(ORM):
    id: int
    user_id: int
    items: List[CartItemResponse]
    created_at: datetime


class OrderItemResponse(ORM):
    id: int
    book_id: int
    price: float
    quantity: int
    book: BookListResponse


class OrderResponse(ORM):
    id: int
    user_id: int
    total_price: float
    status: str
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ── Rentals ───────────────────────────────────────────────────────────────────

class RentOrderCreate(BaseModel):
    book_id: int
    duration: Literal[7, 14, 30]


class RentOrderResponse(ORM):
    id: int
    user_id: int
    book_id: int
    duration: int
    rent_price: float
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    return_date: Optional[datetime]
    created_at: datetime
    book: BookListResponse


# ── AI ────────────────────────────────────────────────────────────────────────

class AIResult(BaseModel):
    """Common envelope: success flag plus either data or an error message."""
    success: bool
    error: Optional[str] = None


class AIBookSummarizeRequest(BaseModel):
    summary_length: Literal["short", "medium", "long"] = "medium"


class AIBookSummarizeResponse(AIResult):
    summary: Optional[str] = None
    length: Optional[str] = None
    words: Optional[int] = None
    estimated_reading_time_minutes: Optional[int] = None


class AIExplainTextRequest(BaseModel):
    book_id: int
    selected_text: str = Field(min_length=1, max_length=2000)


class AIExplainTextResponse(AIResult):
    selected_text: Optional[str] = None
    explanation: Optional[str] = None
    key_concepts: Optional[List[str]] = None
    importance: Optional[str] = None


class AIAskQuestionRequest(BaseModel):
    book_id: int
    question: str = Field(min_length=1, max_length=500)


class AIAskQuestionResponse(AIResult):
    question: Optional[str] = None
    answer: Optional[str] = None
    confidence: Optional[str] = None


class AIKeyConceptsResponse(AIResult):
    main_themes: Optional[List[str]] = None
    key_concepts: Optional[List[str]] = None
    important_topics: Optional[List[str]] = None


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class AIChatResponse(AIResult):
    response: str


# ── Recommendations ───────────────────────────────────────────────────────────

class RecommendationScoreDetail(BaseModel):
    book_id: int
    score: float
    strategy_scores: Dict[str, float]


class BookRecommendationResponse(BaseModel):
    original_book_id: int
    original_book_title: str
    original_book_category: str
    strategies_used: List[str]
    total_candidates_evaluated: int
    recommendations_found: int
    recommendation_scores: List[RecommendationScoreDetail]
    books: List[BookListResponse]


# ── Reviews ───────────────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    book_id: int
    rating: float = Field(ge=1.0, le=5.0)
    title: str = Field(min_length=1, max_length=255)
    content: Optional[str] = None


class ReviewerResponse(ORM):
    id: int
    name: str


class ReviewResponse(ORM):
    id: int
    book_id: int
    user_id: int
    rating: float
    title: str
    content: Optional[str]
    verified_purchase: bool
    created_at: datetime
    updated_at: datetime
    reviewer: Optional[ReviewerResponse] = None


class ReviewListResponse(BaseModel):
    total_reviews: int
    average_rating: float
    reviews: List[ReviewResponse]


# ── Wishlist ──────────────────────────────────────────────────────────────────

class WishlistCreate(BaseModel):
    book_id: int


class WishlistItemResponse(ORM):
    id: int
    user_id: int
    book_id: int
    added_at: datetime
    book: Optional[BookListResponse] = None


class WishlistResponse(BaseModel):
    total_items: int
    items: List[WishlistItemResponse]
