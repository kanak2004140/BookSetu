"""BookSetu API. Also serves the frontend, so the app lives on a single origin."""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import models  # noqa: F401  (registers tables on Base)
from .database import BASE_DIR, Base, engine
from .routers import ai_features, auth, book, cart_order, rental, review, user, wishlist

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BookSetu API", description="Backend API for BookSetu - buy, sell and rent books", version="1.0.0")

for module in (auth, user, book, cart_order, rental, review, wishlist, ai_features):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/pages/index.html")


# Only these folders are public. uploads/pdfs is deliberately not mounted (see /api/books/{id}/pdf).
app.mount("/uploads/images", StaticFiles(directory=BASE_DIR / "uploads" / "images"), name="covers")
for folder in ("pages", "public", "styles"):
    app.mount(f"/{folder}", StaticFiles(directory=BASE_DIR / folder), name=folder)
