from sqlalchemy import Column, DateTime, Integer, String

from ..database import Base, utcnow


class User(Base):
    """User account. role is one of: buyer, seller, admin."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="buyer", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
