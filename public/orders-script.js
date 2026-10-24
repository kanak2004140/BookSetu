/* Orders & rentals page. */

document.addEventListener('DOMContentLoaded', async () => {
    if (!isLoggedIn()) return redirectToLogin();
    await loadOrdersAndRentals();
});

async function loadOrdersAndRentals() {
    try {
        const [orders, rentals] = await Promise.all([api.getOrders(), api.getRentals()]);
        displayOrders(orders);
        displayRentals(rentals);
    } catch (error) {
        showNotification('Failed to load orders and rentals', 'error');
    }
}

function switchTab(tab, button) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    document.getElementById('ordersContainer').style.display = tab === 'orders' ? 'block' : 'none';
    document.getElementById('rentalsContainer').style.display = tab === 'rentals' ? 'block' : 'none';
}

const emptyState = (icon, title, text) => `
    <div class="empty-state">
        <i class="fas ${icon}"></i><h3>${title}</h3><p>${text}</p>
        <a href="books.html" class="btn btn-primary">Browse Books</a>
    </div>`;

function displayOrders(orders) {
    document.getElementById('ordersContainer').innerHTML = orders.length === 0
        ? emptyState('fa-inbox', 'No orders yet', 'Start shopping to place your first order')
        : orders.map(order => `
            <div class="order-card">
                <div class="order-header">
                    <div class="order-info">
                        <h3>Order #${order.id}</h3>
                        <p class="date">Placed on ${new Date(order.created_at + 'Z').toLocaleDateString()}</p>
                    </div>
                    <div class="order-total"><span class="amount">₹${order.total_price.toFixed(2)}</span></div>
                </div>
                <div class="order-status"><span class="status-badge status-${order.status}">${order.status.toUpperCase()}</span></div>
                <div class="order-items">
                    ${order.items.slice(0, 2).map(item => `
                        <div class="order-item-row">
                            <span class="item-title">${escapeHtml(item.book.title)}</span>
                            <span class="item-qty">x${item.quantity}</span>
                            <span class="item-price">₹${item.price.toFixed(2)}</span>
                        </div>`).join('')}
                    ${order.items.length > 2 ? `<div class="order-more">+${order.items.length - 2} more items</div>` : ''}
                </div>
                <div class="order-actions">
                    <a class="btn btn-small btn-outline" href="order-confirmation.html?order_id=${order.id}"><i class="fas fa-eye"></i> View Details</a>
                </div>
            </div>`).join('');
}

function displayRentals(rentals) {
    const date = value => new Date(value + 'Z').toLocaleDateString();
    document.getElementById('rentalsContainer').innerHTML = rentals.length === 0
        ? emptyState('fa-book', 'No rentals yet', 'Rent books and enjoy them for a limited period')
        : rentals.map(rental => `
            <div class="rental-card">
                <div class="rental-header">
                    <h3>${escapeHtml(rental.book.title)}</h3>
                    <span class="status-badge status-${rental.status}">${rental.status.toUpperCase()}</span>
                </div>
                <div class="rental-details">
                    <div class="detail-item"><span class="label">Duration:</span><span>${rental.duration} days</span></div>
                    <div class="detail-item"><span class="label">Rental Price:</span><span>₹${rental.rent_price.toFixed(2)}</span></div>
                    ${rental.end_date ? `<div class="detail-item"><span class="label">Return by:</span><span>${date(rental.end_date)}</span></div>` : ''}
                </div>
                <div class="rental-actions">
                    ${rental.status === 'pending' ? `<button class="btn btn-small btn-primary" onclick="rentalAction(${rental.id}, 'activate')"><i class="fas fa-check"></i> Activate</button>` : ''}
                    ${['active', 'overdue'].includes(rental.status) ? `<button class="btn btn-small btn-primary" onclick="rentalAction(${rental.id}, 'return')"><i class="fas fa-undo"></i> Return</button>` : ''}
                </div>
            </div>`).join('');
}

async function rentalAction(rentalId, action) {
    try {
        await (action === 'activate' ? api.activateRental(rentalId) : api.returnRental(rentalId));
        showNotification(action === 'activate' ? 'Rental activated!' : 'Book returned successfully!');
        await loadOrdersAndRentals();
    } catch (error) {
        showNotification(error.message, 'error');
    }
}
