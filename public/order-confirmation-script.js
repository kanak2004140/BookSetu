/* Order confirmation page. */

document.addEventListener('DOMContentLoaded', async () => {
    if (!isLoggedIn()) return redirectToLogin();

    const orderId = new URLSearchParams(window.location.search).get('order_id');
    if (!orderId) return showError('No order found');
    try {
        displayConfirmation(await api.getOrder(orderId));
    } catch (error) {
        showError('Failed to load order details');
    }
});

function displayConfirmation(order) {
    document.getElementById('confirmationContainer').innerHTML = `
        <div class="confirmation-card">
            <div class="confirmation-header">
                <i class="fas fa-check-circle"></i>
                <h1>Order Confirmed!</h1>
                <p>Thank you for your purchase</p>
            </div>
            <div class="confirmation-details">
                <div class="detail-row"><span class="label">Order ID:</span><span class="value">#${order.id}</span></div>
                <div class="detail-row"><span class="label">Order Date:</span><span class="value">${new Date(order.created_at + 'Z').toLocaleDateString()}</span></div>
                <div class="detail-row"><span class="label">Status:</span><span class="value status-${order.status}">${order.status.toUpperCase()}</span></div>
                <div class="detail-row"><span class="label">Total Amount:</span><span class="value price">₹${order.total_price.toFixed(2)}</span></div>
            </div>
            <div class="confirmation-items">
                <h2>Order Items</h2>
                ${order.items.map(item => `
                    <div class="order-item-summary">
                        <div class="item-info"><h4>${escapeHtml(item.book.title)}</h4><p class="author">${escapeHtml(item.book.author)}</p></div>
                        <div class="item-qty">Qty: ${item.quantity}</div>
                        <div class="item-price">₹${item.price.toFixed(2)}</div>
                    </div>`).join('')}
            </div>
            <div class="confirmation-actions">
                <a href="orders.html" class="btn btn-primary"><i class="fas fa-list"></i> View All Orders</a>
                <a href="books.html" class="btn btn-secondary"><i class="fas fa-book"></i> Continue Shopping</a>
            </div>
        </div>`;
}

function showError(message) {
    document.getElementById('confirmationContainer').innerHTML = `
        <div class="error-card">
            <i class="fas fa-exclamation-circle"></i>
            <h2>${escapeHtml(message)}</h2>
            <a href="books.html" class="btn btn-primary">Back to Books</a>
        </div>`;
}
