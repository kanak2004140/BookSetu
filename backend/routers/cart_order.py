from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Book, Cart, CartItem, Order, OrderItem, OrderStatus, User
from ..schemas import CartItemAdd, CartResponse, OrderResponse, OrderStatusUpdate

router = APIRouter(tags=["Cart & Orders"])


def get_or_create_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


@router.post("/api/cart/add", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    item: CartItemAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not db.query(Book).filter(Book.id == item.book_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Book with ID {item.book_id} not found")
    cart = get_or_create_cart(current_user.id, db)
    existing = db.query(CartItem).filter_by(cart_id=cart.id, book_id=item.book_id).first()
    if existing:
        existing.quantity += item.quantity
    else:
        db.add(CartItem(cart_id=cart.id, book_id=item.book_id, quantity=item.quantity))
    db.commit()
    db.refresh(cart)
    return cart


@router.get("/api/cart", response_model=CartResponse)
def get_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_or_create_cart(current_user.id, db)


@router.delete("/api/cart/remove/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = get_or_create_cart(current_user.id, db)
    item = db.query(CartItem).filter_by(cart_id=cart.id, book_id=book_id).first()
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not in cart")
    db.delete(item)
    db.commit()


@router.post("/api/orders/create", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cart is empty. Add items before creating an order.")

    order = Order(
        user_id=current_user.id,
        total_price=sum(i.book.selling_price * i.quantity for i in cart.items),
        items=[OrderItem(book_id=i.book_id, price=i.book.selling_price, quantity=i.quantity) for i in cart.items],
    )
    db.add(order)
    for item in list(cart.items):
        db.delete(item)
    db.commit()
    db.refresh(order)
    return order


@router.get("/api/orders", response_model=List[OrderResponse])
def get_orders(
    status_filter: Optional[OrderStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Order).filter(Order.user_id == current_user.id)
    if status_filter:
        query = query.filter(Order.status == status_filter.value)
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


def get_order_or_404(order_id: int, db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Order with ID {order_id} not found")
    return order


@router.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = get_order_or_404(order_id, db)
    if order.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only view your own orders")
    return order


@router.patch("/api/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sellers of the ordered books (or admins) set any status; buyers may only cancel a pending order."""
    order = get_order_or_404(order_id, db)
    is_seller = any(item.book.seller_id == current_user.id for item in order.items)
    buyer_cancels = (
        order.user_id == current_user.id
        and order.status == OrderStatus.PENDING.value
        and update.status == OrderStatus.CANCELLED
    )
    if not (current_user.role == "admin" or is_seller or buyer_cancels):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not allowed to change this order's status")
    order.status = update.status.value
    db.commit()
    db.refresh(order)
    return order
