from typing import Literal, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import BASE_DIR, Base, utcnow

Category = Literal["fictional", "academics", "motivational"]
Condition = Literal["new", "like_new", "good", "fair"]


class Book(Base):
    """A book listing. File paths are stored relative to the project root."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    original_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    condition = Column(String(50), nullable=False)
    cover_image_path = Column(String(500), nullable=True)
    pdf_path = Column(String(500), nullable=True)
    is_rentable = Column(Boolean, default=False, nullable=False)
    rent_price = Column(Float, nullable=True)
    bestseller = Column(Boolean, default=False, nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    seller = relationship("User")
    cart_items = relationship("CartItem", back_populates="book", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="book")
    rent_orders = relationship("RentOrder", back_populates="book")

    @property
    def pdf_file(self) -> Optional[str]:
        """Absolute path of the PDF if it exists on disk, else None."""
        if not self.pdf_path:
            return None
        path = BASE_DIR / self.pdf_path
        return str(path) if path.is_file() else None
