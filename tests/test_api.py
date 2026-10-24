from conftest import register

BOOK = {
    "title": "Test Book", "author": "Author", "category": "fictional", "original_price": 200,
    "selling_price": 100, "condition": "new", "is_rentable": True, "rent_price": 20,
}


def test_auth(client):
    headers = register(client, "auth@test.com")
    assert client.get("/api/users/me", headers=headers).json()["email"] == "auth@test.com"
    duplicate = client.post("/api/auth/signup", json={"name": "Test", "email": "auth@test.com", "password": "Passw0rd!"})
    assert duplicate.status_code == 400
    bad_login = client.post("/api/auth/login", json={"email": "auth@test.com", "password": "wrong-password"})
    assert bad_login.status_code == 401
    assert client.get("/api/users/me").status_code == 401


def test_book_validation_and_pdf_access(client):
    seller = register(client, "seller@test.com")
    assert client.post("/api/books", data={**BOOK, "category": "nope"}, headers=seller).status_code == 422
    assert client.post("/api/books", data={**BOOK, "selling_price": -5}, headers=seller).status_code == 422
    bad_upload = client.post("/api/books", data=BOOK, headers=seller, files={"pdf_file": ("x.exe", b"x")})
    assert bad_upload.status_code == 400

    created = client.post("/api/books", data=BOOK, headers=seller, files={"pdf_file": ("../evil.pdf", b"%PDF-1.4")})
    assert created.status_code == 201
    book = created.json()
    assert book["pdf_path"].startswith("uploads/pdfs/") and ".." not in book["pdf_path"]
    assert client.get(f"/api/books/{book['id']}/pdf").status_code == 401
    assert client.get(f"/api/books/{book['id']}/pdf", headers=seller).status_code == 200
    assert client.get(f"/{book['pdf_path']}").status_code == 404  # PDFs are not publicly mounted

    other = register(client, "other@test.com")
    assert client.delete(f"/api/books/{book['id']}", headers=other).status_code == 403


def test_shopping_flow_and_order_permissions(client):
    seller = register(client, "seller2@test.com")
    buyer = register(client, "buyer@test.com")
    book = client.post("/api/books", data=BOOK, headers=seller).json()

    assert client.post("/api/cart/add", json={"book_id": book["id"], "quantity": 0}, headers=buyer).status_code == 422
    client.post("/api/cart/add", json={"book_id": book["id"], "quantity": 2}, headers=buyer)
    assert client.delete(f"/api/cart/remove/{book['id']}", headers=buyer).status_code == 204
    client.post("/api/cart/add", json={"book_id": book["id"], "quantity": 2}, headers=buyer)

    order = client.post("/api/orders/create", headers=buyer).json()
    assert order["total_price"] == 200 and client.get("/api/cart", headers=buyer).json()["items"] == []

    paid = {"status": "paid"}
    assert client.patch(f"/api/orders/{order['id']}/status", json=paid, headers=buyer).status_code == 403
    assert client.patch(f"/api/orders/{order['id']}/status", json=paid, headers=seller).json()["status"] == "paid"
    assert client.delete(f"/api/books/{book['id']}", headers=seller).status_code == 409  # has orders


def test_wishlist_review_and_recommendations(client):
    seller = register(client, "seller3@test.com")
    buyer = register(client, "buyer3@test.com")
    first = client.post("/api/books", data=BOOK, headers=seller).json()
    client.post("/api/books", data={**BOOK, "title": "Second"}, headers=seller)

    item = client.post("/api/wishlist/add", json={"book_id": first["id"]}, headers=buyer).json()
    assert client.post("/api/wishlist/add", json={"book_id": first["id"]}, headers=buyer).status_code == 400
    assert client.post(f"/api/wishlist/{item['id']}/to-cart", headers=buyer).status_code == 200

    review = {"book_id": first["id"], "rating": 4.5, "title": "Good"}
    assert client.post("/api/reviews", json={**review, "rating": 9}, headers=buyer).status_code == 422
    assert client.post("/api/reviews", json=review, headers=buyer).status_code == 201
    assert client.post("/api/reviews", json=review, headers=buyer).status_code == 400
    assert client.get(f"/api/reviews/book/{first['id']}").json()["average_rating"] == 4.5

    recs = client.get(f"/api/books/{first['id']}/recommendations").json()
    assert first["id"] not in [b["id"] for b in recs["books"]] and recs["recommendations_found"] >= 1


def test_rental_lifecycle(client):
    seller = register(client, "seller4@test.com")
    renter = register(client, "renter@test.com")
    book = client.post("/api/books", data=BOOK, headers=seller).json()

    assert client.post("/api/rent", json={"book_id": book["id"], "duration": 5}, headers=renter).status_code == 422
    rental = client.post("/api/rent", json={"book_id": book["id"], "duration": 7}, headers=renter).json()
    assert rental["start_date"] is None and rental["book"]["title"] == "Test Book"
    assert client.patch(f"/api/rent/{rental['id']}/return", headers=renter).status_code == 400  # not active yet

    active = client.patch(f"/api/rent/{rental['id']}/activate", headers=renter).json()
    assert active["status"] == "active" and active["end_date"]
    assert client.patch(f"/api/rent/{rental['id']}/return", headers=renter).json()["status"] == "returned"
    assert client.patch(f"/api/rent/{rental['id']}/return", headers=renter).status_code == 400


def test_ai_endpoints(client):
    headers = register(client, "ai@test.com")
    assert client.post("/api/ai/chat", json={"message": "hi"}).status_code == 401
    reply = client.post("/api/ai/chat", json={"message": "hi"}, headers=headers)
    assert reply.status_code == 200 and "response" in reply.json()
    assert client.get("/api/ai/health").json()["ai_provider"] == "OpenAI"
