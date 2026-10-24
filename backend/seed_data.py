"""Reset the database to sample data: 3 sellers and 7 books.

Run from the project root:  python -m backend.seed_data
WARNING: deletes all existing data.
"""

from .auth import get_password_hash
from .database import BASE_DIR, Base, SessionLocal, engine
from .models import Book, User

SELLERS = [
    ("Rajesh Kumar", "rajesh@booksetu.com", "Seller@123"),
    ("Priya Singh", "priya@booksetu.com", "Seller@456"),
    ("Amit Patel", "amit@booksetu.com", "Seller@789"),
]

# (title, author, category, mrp, price, rent price, description, cover file, pdf file or None)
BOOKS = [
    ("Harry Potter and the Philosopher's Stone", "J.K. Rowling", "fictional", 399, 299, 50,
     "Harry Potter discovers his wizarding powers and attends Hogwarts.", "harrypotter.jpeg", "85jkr_harrypotter_1.pdf"),
    ("The Great Gatsby", "F. Scott Fitzgerald", "fictional", 350, 249, 45,
     "A classic of the Jazz Age exploring love, wealth and the American Dream.", "TheGreatGatsby2013Poster.jpg", None),
    ("Rich Dad Poor Dad", "Robert T. Kiyosaki", "motivational", 450, 349, 60,
     "A guide to building wealth and financial independence.", "71HJj3XmheL._AC_UF1000,1000_QL80_.jpg", None),
    ("The Psychology of Money", "Morgan Housel", "motivational", 499, 379, 65,
     "Timeless lessons on the psychology behind financial success and failure.", "psychology of money.jpg",
     "The-Psychology-of-Money-Morgan-Housel.pdf"),
    ("Atomic Habits", "James Clear", "motivational", 499, 379, 60,
     "Small, consistent changes lead to remarkable results.", "atomic habit.jpeg", None),
    ("Concepts of Physics - Volume 1", "H.C. Verma", "academics", 550, 425, 70,
     "Mechanics and thermodynamics for IIT and competitive exam preparation.", "conceptofphysics1.jpg", None),
    ("Concepts of Physics - Volume 2", "H.C. Verma", "academics", 550, 425, 70,
     "Electricity, magnetism, optics and modern physics.", "conceptofphysics2.jpg", None),
]


def seed_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        sellers = [
            User(name=name, email=email, hashed_password=get_password_hash(password), role="seller")
            for name, email, password in SELLERS
        ]
        db.add_all(sellers)
        db.flush()

        for i, (title, author, category, mrp, price, rent, description, cover, pdf) in enumerate(BOOKS):
            has_pdf = pdf and (BASE_DIR / "uploads" / "pdfs" / pdf).is_file()
            db.add(Book(
                title=title, author=author, category=category, original_price=mrp, selling_price=price,
                condition="new", description=description, is_rentable=True, rent_price=rent, bestseller=True,
                cover_image_path=f"uploads/images/{cover}",
                pdf_path=f"uploads/pdfs/{pdf}" if has_pdf else None,
                seller_id=sellers[i % len(sellers)].id,
            ))
        db.commit()
        print(f"Seeded {len(sellers)} sellers and {len(BOOKS)} books.")
        for name, email, password in SELLERS:
            print(f"  {email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
