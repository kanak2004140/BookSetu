from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db, utcnow
from ..models import Book, RentOrder, RentStatus, User
from ..schemas import RentOrderCreate, RentOrderResponse

router = APIRouter(prefix="/api/rent", tags=["Rentals"])


def mark_overdue(rentals: List[RentOrder], db: Session) -> None:
    """Active rentals past their end date become 'overdue'."""
    now = utcnow()
    changed = False
    for rental in rentals:
        if rental.status == RentStatus.ACTIVE.value and rental.end_date and now > rental.end_date:
            rental.status = RentStatus.OVERDUE.value
            changed = True
    if changed:
        db.commit()


def get_own_rental(rental_id: int, db: Session, user: User) -> RentOrder:
    rental = db.query(RentOrder).filter(RentOrder.id == rental_id).first()
    if not rental:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Rental with ID {rental_id} not found")
    if rental.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only access your own rentals")
    mark_overdue([rental], db)
    return rental


@router.post("", response_model=RentOrderResponse, status_code=status.HTTP_201_CREATED)
def create_rental(
    rental: RentOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == rental.book_id).first()
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book with ID {rental.book_id} not found")
    if not book.is_rentable or book.rent_price is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This book is not available for rental")

    order = RentOrder(
        user_id=current_user.id, book_id=book.id, duration=rental.duration, rent_price=book.rent_price
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=List[RentOrderResponse])
def get_rentals(
    status_filter: Optional[RentStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(RentOrder).filter(RentOrder.user_id == current_user.id)
    rentals = query.order_by(RentOrder.created_at.desc()).offset(skip).limit(limit).all()
    mark_overdue(rentals, db)
    if status_filter:
        rentals = [r for r in rentals if r.status == status_filter.value]
    return rentals


@router.get("/{rental_id}", response_model=RentOrderResponse)
def get_rental(rental_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_own_rental(rental_id, db, current_user)


@router.patch("/{rental_id}/activate", response_model=RentOrderResponse)
def activate_rental(rental_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Start the rental period (called once payment is confirmed)."""
    rental = get_own_rental(rental_id, db, current_user)
    if rental.status != RentStatus.PENDING.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Can only activate pending rentals. Current status: {rental.status}")
    rental.status = RentStatus.ACTIVE.value
    rental.start_date = utcnow()
    rental.end_date = rental.start_date + timedelta(days=rental.duration)
    db.commit()
    db.refresh(rental)
    return rental


@router.patch("/{rental_id}/return", response_model=RentOrderResponse)
def return_rental(rental_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rental = get_own_rental(rental_id, db, current_user)
    if rental.status not in (RentStatus.ACTIVE.value, RentStatus.OVERDUE.value):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Only active or overdue rentals can be returned. Current status: {rental.status}")
    rental.status = RentStatus.RETURNED.value
    rental.return_date = utcnow()
    db.commit()
    db.refresh(rental)
    return rental
