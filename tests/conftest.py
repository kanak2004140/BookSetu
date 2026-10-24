import os
import tempfile

# Must be set before the backend is imported.
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["OPENAI_API_KEY"] = ""  # keep tests offline (load_dotenv never overrides existing vars)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.database import BASE_DIR, SessionLocal  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import Book  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
    with SessionLocal() as db:  # remove files uploaded during the tests
        for book in db.query(Book):
            for path in (book.pdf_path, book.cover_image_path):
                if path:
                    (BASE_DIR / path).unlink(missing_ok=True)


def register(client, email, role=None):
    """Create a user (optionally promote to `role`) and return auth headers."""
    client.post("/api/auth/signup", json={"name": "Test User", "email": email, "password": "Passw0rd!"})
    if role:
        from backend.database import SessionLocal
        from backend.models import User

        with SessionLocal() as db:
            db.query(User).filter_by(email=email).update({"role": role})
            db.commit()
    token = client.post("/api/auth/login", json={"email": email, "password": "Passw0rd!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
