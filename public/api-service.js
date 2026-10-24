/* Shared API client and helpers. Same origin as the backend, so the base URL is relative. */

const API_BASE_URL = '/api';

const PLACEHOLDER_COVER = 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="300"><rect width="200" height="300" fill="#e8f1ec"/>' +
    '<text x="100" y="155" font-family="sans-serif" font-size="20" fill="#6fa582" text-anchor="middle">No cover</text></svg>'
);

/** Escape text before putting it into innerHTML. */
function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function coverUrl(book) {
    return book.cover_image_path ? '/' + book.cover_image_path : PLACEHOLDER_COVER;
}

class BookSetuAPI {
    get token() {
        return localStorage.getItem('access_token');
    }

    async request(endpoint, { method = 'GET', body } = {}) {
        const headers = {};
        if (this.token) headers.Authorization = `Bearer ${this.token}`;
        if (body !== undefined && !(body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            body = JSON.stringify(body);
        }

        const response = await fetch(API_BASE_URL + endpoint, { method, headers, body });

        // An expired/invalid token sends the user back to login; a failed login attempt (no token) must not.
        if (response.status === 401 && this.token) {
            localStorage.removeItem('access_token');
            redirectToLogin();
            throw new Error('Session expired. Please login again.');
        }
        const data = response.status === 204 ? null : await response.json();
        if (!response.ok) {
            const detail = data && data.detail;
            throw new Error(Array.isArray(detail) ? detail[0].msg : detail || `HTTP ${response.status}`);
        }
        return data;
    }

    // Auth
    signup(name, email, password) { return this.request('/auth/signup', { method: 'POST', body: { name, email, password } }); }
    login(email, password) { return this.request('/auth/login', { method: 'POST', body: { email, password } }); }
    getCurrentUser() { return this.request('/users/me'); }

    // Books
    createBook(formData) { return this.request('/books', { method: 'POST', body: formData }); }
    getBook(id) { return this.request(`/books/${id}`); }
    getBooks({ category, sellerId, limit = 100 } = {}) {
        const params = new URLSearchParams({ limit });
        if (category) params.set('category', category);
        if (sellerId) params.set('seller_id', sellerId);
        return this.request(`/books?${params}`);
    }

    // Cart & orders
    getCart() { return this.request('/cart'); }
    addToCart(bookId, quantity = 1) { return this.request('/cart/add', { method: 'POST', body: { book_id: bookId, quantity } }); }
    removeFromCart(bookId) { return this.request(`/cart/remove/${bookId}`, { method: 'DELETE' }); }
    createOrder() { return this.request('/orders/create', { method: 'POST' }); }
    getOrders() { return this.request('/orders'); }
    getOrder(id) { return this.request(`/orders/${id}`); }

    // Rentals
    createRental(bookId, duration) { return this.request('/rent', { method: 'POST', body: { book_id: bookId, duration } }); }
    getRentals() { return this.request('/rent'); }
    getRental(id) { return this.request(`/rent/${id}`); }
    activateRental(id) { return this.request(`/rent/${id}/activate`, { method: 'PATCH' }); }
    returnRental(id) { return this.request(`/rent/${id}/return`, { method: 'PATCH' }); }

    // AI
    summarizeBook(id, summary_length = 'medium') { return this.request(`/ai/summarize-book/${id}`, { method: 'POST', body: { summary_length } }); }
    chat(message) { return this.request('/ai/chat', { method: 'POST', body: { message } }); }
}

const api = new BookSetuAPI();

function isLoggedIn() {
    return localStorage.getItem('access_token') !== null;
}

function redirectToLogin() {
    window.location.href = '/pages/login.html';
}

function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `position:fixed;top:20px;right:20px;padding:15px 20px;border-radius:4px;color:#fff;z-index:10000;
        background:${type === 'success' ? '#4caf50' : '#f44336'};transition:opacity .3s`;
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}
