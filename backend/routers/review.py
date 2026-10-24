from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Book, Order, OrderItem, OrderStatus, Review, User
from ..schemas import ReviewCreate, ReviewListResponse, ReviewResponse

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


def get_review_or_404(review_id: int, db: Session) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return review


def get_own_review(review_id: int, db: Session, user: User) -> Review:
    review = get_review_or_404(review_id, db)
    if review.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only modify your own reviews")
    return review


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not db.query(Book).filter(Book.id == data.book_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    if db.query(Review).filter_by(book_id=data.book_id, user_id=current_user.id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You have already reviewed this book. Update your review instead.")

    purchased = (
        db.query(OrderItem).join(Order)
        .filter(
            Order.user_id == current_user.id,
            OrderItem.book_id == data.book_id,
            Order.status == OrderStatus.COMPLETED.value,
        )
        .first()
    )
    review = Review(**data.model_dump(), user_id=current_user.id, verified_purchase=purchased is not None)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/book/{book_id}", response_model=ReviewListResponse)
def get_book_reviews(
    book_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    if not db.query(Book).filter(Book.id == book_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    approved = db.query(Review).filter(Review.book_id == book_id, Review.is_approved.is_(True))
    total, average = approved.with_entities(func.count(Review.id), func.avg(Review.rating)).one()
    reviews = approved.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    return ReviewListResponse(total_reviews=total, average_rating=float(average or 0), reviews=reviews)


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    return get_review_or_404(review_id, db)


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = get_own_review(review_id, db, current_user)
    review.rating, review.title, review.content = data.rating, data.title, data.content
    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(get_own_review(review_id, db, current_user))
    db.commit()
