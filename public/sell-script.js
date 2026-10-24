/* Sell page: list a book (with optional cover image, PDF and rental price). */

document.addEventListener('DOMContentLoaded', () => {
    if (!isLoggedIn()) return redirectToLogin();

    const rentable = document.getElementById('is-rentable');
    const rentPrice = document.getElementById('rent-price');
    rentable.addEventListener('change', () => {
        document.getElementById('rent-price-wrapper').style.display = rentable.checked ? 'flex' : 'none';
        rentPrice.required = rentable.checked;
    });

    initCoverUpload();
    document.getElementById('sell-form').addEventListener('submit', submitBook);
});

function initCoverUpload() {
    const input = document.getElementById('book-image');
    const area = document.querySelector('.file-upload-area');
    const showFile = () => {
        if (input.files[0]) area.querySelector('p').textContent = input.files[0].name;
    };
    area.addEventListener('click', () => input.click());
    area.addEventListener('dragover', e => e.preventDefault());
    area.addEventListener('drop', e => {
        e.preventDefault();
        input.files = e.dataTransfer.files;
        showFile();
    });
    input.addEventListener('change', showFile);
}

async function submitBook(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector('.btn-submit');
    const field = id => document.getElementById(id);

    const data = new FormData();
    data.append('title', field('book-name').value);
    data.append('author', field('author-name').value);
    data.append('category', field('category').value);
    data.append('original_price', field('mrp').value);
    data.append('selling_price', field('selling-price').value);
    data.append('condition', form.querySelector('input[name="condition"]:checked').value);
    data.append('description', field('description').value);
    data.append('is_rentable', field('is-rentable').checked);
    if (field('is-rentable').checked) data.append('rent_price', field('rent-price').value);
    for (const [name, id] of [['cover_image', 'book-image'], ['pdf_file', 'book-pdf']]) {
        if (field(id).files.length) data.append(name, field(id).files[0]);
    }

    button.disabled = true;
    try {
        const book = await api.createBook(data);
        showNotification(`Book "${book.title}" listed successfully!`);
        setTimeout(() => { window.location.href = 'books.html'; }, 1500);
    } catch (error) {
        showNotification(error.message, 'error');
        button.disabled = false;
    }
}
