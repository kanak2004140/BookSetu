/* Cart page: list items, change quantity, remove, checkout. */

let cartData = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!isLoggedIn()) return redirectToLogin();
    await loadCart();
});

async function loadCart() {
    try {
        cartData = await api.getCart();
        renderCart();
    } catch (error) {
        showNotification('Failed to load cart', 'error');
    }
}

function renderCart() {
    const container = document.getElementById('cartContainer');
    if (cartData.items.length === 0) {
        container.innerHTML = `
            <div class="empty-cart">
                <i class="fas fa-shopping-cart"></i>
                <h2>Your cart is empty</h2>
                <p>Start shopping by browsing our collection of books</p>
                <a href="books.html" class="btn btn-primary">Continue Shopping</a>
            </div>`;
        return;
    }

    const total = cartData.items.reduce((sum, item) => sum + item.book.selling_price * item.quantity, 0);
    container.innerHTML = `
        <div class="cart-items">
            ${cartData.items.map(item => `
                <div class="cart-item">
                    <div class="cart-item-image"><img src="${coverUrl(item.book)}" alt="${escapeHtml(item.book.title)}"></div>
                    <div class="cart-item-details">
                        <h4>${escapeHtml(item.book.title)}</h4>
                        <p class="author">${escapeHtml(item.book.author)}</p>
                        <p class="condition">Condition: ${escapeHtml(item.book.condition.replace('_', ' '))}</p>
                    </div>
                    <div class="cart-item-price"><p class="price">₹${item.book.selling_price.toFixed(2)}</p></div>
                    <div class="cart-item-quantity">
                        <button class="qty-btn" onclick="updateQuantity(${item.book_id}, ${item.quantity - 1})">-</button>
                        <span>${item.quantity}</span>
                        <button class="qty-btn" onclick="updateQuantity(${item.book_id}, ${item.quantity + 1})">+</button>
                    </div>
                    <div class="cart-item-total"><p class="total">₹${(item.book.selling_price * item.quantity).toFixed(2)}</p></div>
                    <button class="remove-btn" onclick="removeFromCart(${item.book_id})"><i class="fas fa-trash"></i></button>
                </div>`).join('')}
        </div>
        <div class="cart-summary">
            <div class="summary-row"><span>Subtotal:</span><span>₹${total.toFixed(2)}</span></div>
            <div class="summary-row"><span>Shipping:</span><span>Free</span></div>
            <div class="summary-row total"><span>Total:</span><span>₹${total.toFixed(2)}</span></div>
            <button class="btn btn-primary btn-block" onclick="checkout()"><i class="fas fa-lock"></i> Place Order</button>
            <a href="books.html" class="btn btn-secondary btn-block">Continue Shopping</a>
        </div>`;
}

async function removeFromCart(bookId) {
    try {
        await api.removeFromCart(bookId);
        await loadCart();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function updateQuantity(bookId, quantity) {
    if (quantity < 1) return removeFromCart(bookId);
    try {
        await api.removeFromCart(bookId);
        await api.addToCart(bookId, quantity);
        await loadCart();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function checkout() {
    try {
        const order = await api.createOrder();
        window.location.href = `order-confirmation.html?order_id=${order.id}`;
    } catch (error) {
        showNotification('Checkout failed: ' + error.message, 'error');
    }
}
