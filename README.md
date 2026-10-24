# BookSetu Library

A marketplace for buying, selling and renting books, with a PDF reader and an AI reading companion (PadhAI).
FastAPI + SQLite backend that also serves a plain HTML/CSS/JS frontend, so the whole app runs from one server.

## Run it

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env            # then set SECRET_KEY (and OPENAI_API_KEY for AI features)
python -m backend.seed_data       # optional: sample sellers and books (wipes existing data)
python -m uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000 (the app) or http://127.0.0.1:8000/docs (API docs).
Seeded accounts: `rajesh@booksetu.com / Seller@123`, `priya@booksetu.com / Seller@456`, `amit@booksetu.com / Seller@789`.

Tests: `python -m pytest tests`

## Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | **Required.** Signs login tokens. |
| `TOKEN_EXPIRATION_MINUTES` | Token lifetime (default 30). |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | AI features. Without a valid key the AI endpoints return an error message. |
| `DATABASE_URL` | Optional. Defaults to `booksetu.db` (SQLite) in the project root. |

## Features

- **Accounts**: signup, login (JWT), profile with real activity counts.
- **Books**: list with cover image and optional PDF, browse by category (`fictional`, `academics`, `motivational`), details modal.
- **Cart and orders**: cart, checkout, order history. Sellers (or admins) update order status; buyers can cancel a pending order. There is no payment gateway.
- **Rentals**: rent for 7/14/30 days, activate, return; active rentals past their end date show as `overdue`.
- **Reviews and wishlist**: API only (no UI yet).
- **Reading**: authenticated PDF viewer (PDFs are never served as public files).
- **AI** (OpenAI): book summaries, passage explanations, Q&A, key concepts, PadhAI chat.
- **Recommendations**: `GET /api/books/{id}/recommendations` (category, price, collaborative and popularity scores).

## Layout

```
backend/   main.py (app + static mounts), database.py, auth.py, schemas.py, seed_data.py,
           models/, routers/ (auth, user, book, cart_order, rental, review, wishlist, ai_features),
           services/ (ai_service, recommendation_service)
pages/     HTML pages          public/   JS (api-service.js is the shared client)
styles/    CSS                 tests/    pytest suite
uploads/   images/ (public covers), pdfs/ (served only through /api/books/{id}/pdf)
```

Only `pages/`, `public/`, `styles/` and `uploads/images/` are exposed over HTTP; `.env` and the database are not.

## Known limitations

- No schema migrations: `create_all` creates missing tables but does not alter existing ones. Re-run the seed script (or delete `booksetu.db`) after model changes.
- No payments, email notifications, rate limiting, or pagination UI (the books page loads the first 100 books).
- `backend/.env` is no longer read. It still holds an old Google key and a weak secret; delete it once you no longer need that key.
- Docker: `docker build -t booksetu .` then `docker run -p 8000:8000 --env-file .env booksetu`. Uploaded files and the database live inside the container unless you mount volumes.
