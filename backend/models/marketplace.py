import enum

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base, utcnow


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1, nullable=False)

    cart = relationship("Cart", back_populates="items")
    book = relationship("Book", back_populates="cart_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), default=OrderStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)  # price at time of purchase
    quantity = Column(Integer, default=1, nullable=False)

    order = relationship("Order", back_populates="items")
    book = relationship("Book", back_populates="order_items")


class RentOrder(Base):
    __tablename__ = "rent_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    duration = Column(Integer, nullable=False)  # days: 7, 14 or 30
    rent_price = Column(Float, nullable=False)
    status = Column(String(50), default=RentStatus.PENDING.value, nullable=False)
    start_date = Column(DateTime, nullable=True)  # set on activation
    end_date = Column(DateTime, nullable=True)
    return_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    book = relationship("Book", back_populates="rent_orders")
