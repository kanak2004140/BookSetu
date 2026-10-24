"""Book recommendations: weighted mix of category, price, collaborative and popularity scores."""

import math
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Book, Order, OrderItem

WEIGHTS = {"category": 0.40, "price": 0.20, "collaborative": 0.20, "popularity": 0.20}


class RecommendationService:
    @classmethod
    def get_recommendations(
        cls, db: Session, book: Book, limit: int = 10, strategies: Optional[List[str]] = None
    ) -> Tuple[List[Book], Dict[str, Any]]:
        strategies = [s for s in (strategies or []) if s in WEIGHTS] or list(WEIGHTS)
        candidates = db.query(Book).filter(Book.id != book.id).all()

        popularity = dict(
            db.query(OrderItem.book_id, func.count(OrderItem.id)).group_by(OrderItem.book_id).all()
        ) if "popularity" in strategies else {}
        co_bought, total_buyers = cls._collaborative_counts(db, book) if "collaborative" in strategies else ({}, 0)

        scored = []
        for candidate in candidates:
            parts = {}
            if "category" in strategies:
                parts["category"] = float(book.category.lower() == candidate.category.lower())
            if "price" in strategies:
                parts["price"] = cls._price_score(book.selling_price, candidate.selling_price)
            if "collaborative" in strategies:
                parts["collaborative"] = min(co_bought.get(candidate.id, 0) / total_buyers, 1.0) if total_buyers else 0.0
            if "popularity" in strategies:
                parts["popularity"] = min(math.log(1 + popularity.get(candidate.id, 0)) / math.log(101), 1.0)
            score = sum(WEIGHTS[name] * value for name, value in parts.items())
            scored.append((score, candidate, parts))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:limit]
        metadata = {
            "original_book_id": book.id,
            "original_book_title": book.title,
            "original_book_category": book.category,
            "strategies_used": strategies,
            "total_candidates_evaluated": len(candidates),
            "recommendations_found": len(top),
            "recommendation_scores": [
                {
                    "book_id": candidate.id,
                    "score": round(score, 2),
                    "strategy_scores": {name: round(value, 2) for name, value in parts.items()},
                }
                for score, candidate, parts in top
            ],
        }
        return [candidate for _, candidate, _ in top], metadata

    @staticmethod
    def _price_score(current: float, candidate: float) -> float:
        average = (current + candidate) / 2
        if average == 0:
            return 1.0
        return math.exp(-abs(current - candidate) / (average * 0.5))

    @staticmethod
    def _collaborative_counts(db: Session, book: Book) -> Tuple[Dict[int, int], int]:
        """Return ({book_id: times bought by users who bought `book`}, number of such orders)."""
        buyers = (
            db.query(Order.user_id).join(OrderItem).filter(OrderItem.book_id == book.id).subquery()
        )
        co_bought = dict(
            db.query(OrderItem.book_id, func.count(OrderItem.id))
            .join(Order)
            .filter(Order.user_id.in_(db.query(buyers.c.user_id)), OrderItem.book_id != book.id)
            .group_by(OrderItem.book_id)
            .all()
        )
        total = db.query(func.count(OrderItem.id)).filter(OrderItem.book_id == book.id).scalar() or 0
        return co_bought, total
