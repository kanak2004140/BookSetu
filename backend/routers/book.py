import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import BASE_DIR, get_db
from ..models import Book, OrderItem, RentOrder, User
from ..models.book import Category, Condition
from ..schemas import BookListResponse, BookRecommendationResponse, BookResponse
from ..services import RecommendationService

router = APIRouter(prefix="/api/books", tags=["Books"])

IMAGE_DIR = "uploads/images"
PDF_DIR = "uploads/pdfs"
for _dir in (IMAGE_DIR, PDF_DIR):
    (BASE_DIR / _dir).mkdir(parents=True, exist_ok=True)


def save_upload(file: UploadFile, directory: str, extensions: set, max_mb: int) -> str:
    """Validate and store an upload under a random name; returns the relative path."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in extensions:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Allowed file types: {', '.join(sorted(extensions))}")
    data = file.file.read(max_mb * 1024 * 1024 + 1)
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"File too large (max {max_mb}MB)")
    relative = f"{directory}/{uuid.uuid4().hex}{ext}"
    (BASE_DIR / relative).write_bytes(data)
    return relative


def save_cover(file: UploadFile) -> str:
    return save_upload(file, IMAGE_DIR, {".jpg", ".jpeg", ".png", ".webp"}, 5)


def save_pdf(file: UploadFile) -> str:
    return save_upload(file, PDF_DIR, {".pdf"}, 50)


def delete_file(relative: Optional[str]) -> None:
    if relative:
        (BASE_DIR / relative).unlink(missing_ok=True)


def get_book_or_404(book_id: int, db: Session) -> Book:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book with ID {book_id} not found")
    return book


def get_own_book(book_id: int, db: Session, user: User) -> Book:
    book = get_book_or_404(book_id, db)
    if book.seller_id != user.id and user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only modify your own book listings")
    return book


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    title: str = Form(..., min_length=1),
    author: str = Form(..., min_length=1),
    category: Category = Form(...),
    original_price: float = Form(..., gt=0),
    selling_price: float = Form(..., gt=0),
    condition: Condition = Form(...),
    description: Optional[str] = Form(None),
    is_rentable: bool = Form(False),
    rent_price: Optional[float] = Form(None, gt=0),
    cover_image: Optional[UploadFile] = File(None),
    pdf_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if is_rentable and rent_price is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "rent_price is required for rentable books")

    cover_path = save_cover(cover_image) if cover_image else None
    try:
        pdf_path = save_pdf(pdf_file) if pdf_file else None
    except HTTPException:
        delete_file(cover_path)
        raise

    book = Book(
        title=title, author=author, category=category, original_price=original_price,
        selling_price=selling_price, condition=condition, description=description,
        cover_image_path=cover_path, pdf_path=pdf_path, is_rentable=is_rentable,
        rent_price=rent_price if is_rentable else None, seller_id=current_user.id,
    )
    db.add(book)
    try:
        db.commit()
    except Exception:
        db.rollback()
        delete_file(cover_path)
        delete_file(pdf_path)
        raise
    db.refresh(book)
    return book


@router.get("", response_model=List[BookListResponse])
def get_books(
    category: Optional[Category] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    seller_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if category:
        query = query.filter(Book.category == category)
    if min_price is not None:
        query = query.filter(Book.selling_price >= min_price)
    if max_price is not None:
        query = query.filter(Book.selling_price <= max_price)
    if seller_id:
        query = query.filter(Book.seller_id == seller_id)
    return query.order_by(Book.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    return get_book_or_404(book_id, db)


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    title: Optional[str] = Form(None, min_length=1),
    author: Optional[str] = Form(None, min_length=1),
    category: Optional[Category] = Form(None),
    original_price: Optional[float] = Form(None, gt=0),
    selling_price: Optional[float] = Form(None, gt=0),
    condition: Optional[Condition] = Form(None),
    description: Optional[str] = Form(None),
    is_rentable: Optional[bool] = Form(None),
    rent_price: Optional[float] = Form(None, gt=0),
    cover_image: Optional[UploadFile] = File(None),
    pdf_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = get_own_book(book_id, db, current_user)

    fields = dict(
        title=title, author=author, category=category, original_price=original_price,
        selling_price=selling_price, condition=condition, description=description,
        is_rentable=is_rentable, rent_price=rent_price,
    )
    for name, value in fields.items():
        if value is not None:
            setattr(book, name, value)
    if book.is_rentable and book.rent_price is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "rent_price is required for rentable books")

    old_files = []
    if cover_image:
        old_files.append(book.cover_image_path)
        book.cover_image_path = save_cover(cover_image)
    if pdf_file:
        old_files.append(book.pdf_path)
        book.pdf_path = save_pdf(pdf_file)

    db.commit()
    for path in old_files:
        delete_file(path)
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = get_own_book(book_id, db, current_user)
    if db.query(OrderItem).filter_by(book_id=book_id).first() or db.query(RentOrder).filter_by(book_id=book_id).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "This book has orders or rentals and cannot be deleted")
    cover, pdf = book.cover_image_path, book.pdf_path
    db.delete(book)
    db.commit()
    delete_file(cover)
    delete_file(pdf)


@router.get("/{book_id}/pdf", response_class=FileResponse)
def get_book_pdf(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Serve the book PDF to logged-in users (PDFs are not publicly mounted)."""
    pdf = get_book_or_404(book_id, db).pdf_file
    if not pdf:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF not available for this book")
    return FileResponse(pdf, media_type="application/pdf")


@router.get("/{book_id}/recommendations", response_model=BookRecommendationResponse)
def get_book_recommendations(
    book_id: int,
    limit: int = Query(10, ge=1, le=20),
    strategies: Optional[List[str]] = Query(None, description="category, price, collaborative, popularity"),
    db: Session = Depends(get_db),
):
    book = get_book_or_404(book_id, db)
    books, metadata = RecommendationService.get_recommendations(db, book, limit, strategies)
    return BookRecommendationResponse(books=books, **metadata)
