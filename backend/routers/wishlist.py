from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Book, Cart, CartItem, User, Wishlist
from ..schemas import WishlistCreate, WishlistItemResponse, WishlistResponse

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


def get_own_item(wishlist_id: int, db: Session, user: User) -> Wishlist:
    item = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Wishlist item not found")
    if item.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only modify your own wishlist")
    return item


@router.get("", response_model=WishlistResponse)
def get_wishlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(Wishlist).filter(Wishlist.user_id == current_user.id).all()
    return WishlistResponse(total_items=len(items), items=items)


@router.post("/add", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    data: WishlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not db.query(Book).filter(Book.id == data.book_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")
    if db.query(Wishlist).filter_by(user_id=current_user.id, book_id=data.book_id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Book is already in your wishlist")
    item = Wishlist(user_id=current_user.id, book_id=data.book_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    wishlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.delete(get_own_item(wishlist_id, db, current_user))
    db.commit()


@router.post("/{wishlist_id}/to-cart")
def move_to_cart(
    wishlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = get_own_item(wishlist_id, db, current_user)
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.flush()
    cart_item = db.query(CartItem).filter_by(cart_id=cart.id, book_id=item.book_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        db.add(CartItem(cart_id=cart.id, book_id=item.book_id, quantity=1))
    book_id = item.book_id
    db.delete(item)
    db.commit()
    return {"message": "Book moved to cart successfully", "book_id": book_id}
