/* Books page: catalogue, category filter, details modal, cart, PDF reader, AI summary and rentals. */

let allBooks = [];

document.addEventListener('DOMContentLoaded', async () => {
    await loadBooks();
    initFilters();
    initModal();
});

async function loadBooks() {
    const grid = document.getElementById('booksGrid');
    grid.innerHTML = '<div class="loading">Loading books...</div>';
    try {
        allBooks = await api.getBooks();
        renderBooks(allBooks);
    } catch (error) {
        grid.innerHTML = '<div class="error-message">Failed to load books. Please try again.</div>';
    }
}

function renderBooks(books) {
    const grid = document.getElementById('booksGrid');
    if (books.length === 0) {
        grid.innerHTML = '<div class="no-books">No books found in this category.</div>';
        return;
    }
    grid.innerHTML = books.map(book => `
        <div class="book-card">
            <div class="book-image">
                <img src="${coverUrl(book)}" alt="${escapeHtml(book.title)}">
                <div class="condition-badge">${escapeHtml(book.condition.replace('_', ' '))}</div>
                ${book.is_rentable ? '<div class="rental-badge">Rentable</div>' : ''}
            </div>
            <div class="book-details">
                <h3 class="book-title">${escapeHtml(book.title)}</h3>
                <p class="book-author">by ${escapeHtml(book.author)}</p>
                <p class="book-category"><i class="fas fa-tag"></i> ${escapeHtml(book.category)}</p>
                <div class="book-price"><span class="selling-price">₹${book.selling_price.toFixed(2)}</span></div>
                <div class="book-actions">
                    <button class="btn btn-small btn-primary" onclick="viewBookDetails(${book.id})"><i class="fas fa-eye"></i> View</button>
                    <button class="btn btn-small btn-secondary" onclick="addToCart(${book.id})"><i class="fas fa-shopping-cart"></i> Cart</button>
                    ${book.pdf_path ? `
                        <button class="btn btn-small btn-outline" onclick="readOnline(${book.id})"><i class="fas fa-book"></i> Read</button>
                        <button class="btn btn-small btn-accent" onclick="readWithAI(${book.id})"><i class="fas fa-brain"></i> AI</button>` : ''}
                </div>
            </div>
        </div>`).join('');
}

function initFilters() {
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(button => button.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        button.classList.add('active');
        const category = button.dataset.category;
        renderBooks(category === 'all' ? allBooks : allBooks.filter(book => book.category === category));
    }));
}

// ── Modal ─────────────────────────────────────────────────────────────────────

function initModal() {
    const overlay = document.getElementById('readingModalOverlay');
    document.getElementById('closeModalBtn').addEventListener('click', closeModal);
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
}

function openModal(title, subtitle, html) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalAuthor').textContent = subtitle;
    document.getElementById('modalContent').innerHTML = html;
    document.getElementById('readingModalOverlay').style.display = 'flex';
}

function closeModal() {
    document.getElementById('readingModalOverlay').style.display = 'none';
}

function setModalButton(label, onClick) {
    const button = document.getElementById('buyModalBtn');
    button.textContent = label;
    button.onclick = onClick;
}

async function viewBookDetails(bookId) {
    try {
        const book = await api.getBook(bookId);
        const rent = book.is_rentable ? `
            <p><strong>Rent:</strong> ₹${book.rent_price}
                <select id="rentDuration"><option value="7">7 days</option><option value="14">14 days</option><option value="30">30 days</option></select>
                <button class="btn btn-small btn-secondary" onclick="rentBook(${book.id})">Rent</button></p>` : '';
        openModal(book.title, `by ${book.author}`, `
            <div class="modal-book-details">
                <div class="modal-book-image"><img src="${coverUrl(book)}" alt="${escapeHtml(book.title)}"></div>
                <div class="modal-book-info">
                    <p><strong>Category:</strong> ${escapeHtml(book.category)}</p>
                    <p><strong>Condition:</strong> ${escapeHtml(book.condition.replace('_', ' '))}</p>
                    <p><strong>Price:</strong> ₹${book.selling_price}</p>
                    ${rent}
                    <p><strong>Description:</strong></p>
                    <p>${escapeHtml(book.description || 'No description available.')}</p>
                </div>
            </div>`);
        setModalButton(`Add to Cart - ₹${book.selling_price}`, () => { addToCart(bookId); closeModal(); });
    } catch (error) {
        showNotification('Failed to load book details', 'error');
    }
}

// ── Actions ───────────────────────────────────────────────────────────────────

async function addToCart(bookId) {
    if (!isLoggedIn()) return redirectToLogin();
    try {
        await api.addToCart(bookId, 1);
        showNotification('Book added to cart!');
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function rentBook(bookId) {
    if (!isLoggedIn()) return redirectToLogin();
    try {
        await api.createRental(bookId, Number(document.getElementById('rentDuration').value));
        closeModal();
        showNotification('Rental created. Activate it from the Orders page.');
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function readOnline(bookId) {
    const book = allBooks.find(b => b.id === bookId);
    window.open(`/pages/pdf-viewer.html?book=${bookId}&title=${encodeURIComponent(book.title)}`, '_blank');
}

async function readWithAI(bookId) {
    if (!isLoggedIn()) return redirectToLogin();
    const book = allBooks.find(b => b.id === bookId);
    openModal(`AI Summary - ${book.title}`, 'Generating summary...', '<div class="loading"><i class="fas fa-brain"></i> AI is reading this book...</div>');
    setModalButton('Read Full PDF', () => readOnline(bookId));
    try {
        const result = await api.summarizeBook(bookId);
        document.getElementById('modalAuthor').textContent = `by ${book.author}`;
        document.getElementById('modalContent').innerHTML = result.success
            ? `<h3>AI-Generated Summary</h3><p>${escapeHtml(result.summary).replace(/\n/g, '<br>')}</p>
               <small>About ${result.estimated_reading_time_minutes} min read</small>`
            : `<div class="error-message">${escapeHtml(result.error)}</div>`;
    } catch (error) {
        closeModal();
        showNotification(error.message, 'error');
    }
}
