/* Shared page behaviour: scroll animations, mobile menu, password toggles, newsletter and the login/signup forms.
   Requires gsap, ScrollTrigger and api-service.js. */

document.addEventListener('DOMContentLoaded', () => {
    initAnimations();
    initMobileMenu();
    initPasswordToggles();
    initAuthForms();
    initNewsletter();
    initRecommendations();
});

/** Homepage: show the latest listings. */
async function initRecommendations() {
    const grid = document.getElementById('recommendedGrid');
    if (!grid) return;
    try {
        const books = await api.getBooks({ limit: 4 });
        grid.innerHTML = books.map(book => `
            <a class="book-card" href="books.html">
                <div class="book-image"><img src="${coverUrl(book)}" alt="${escapeHtml(book.title)}"></div>
                <div class="book-info">
                    <h3 class="book-title">${escapeHtml(book.title)}</h3>
                    <p class="book-author">${escapeHtml(book.author)}</p>
                    <div class="book-rating"><span class="price">₹${book.selling_price}</span></div>
                </div>
            </a>`).join('');
    } catch (error) {
        grid.innerHTML = '';
    }
}

// ── Animations ────────────────────────────────────────────────────────────────

function reveal(selector, { y = 30, stagger = 0.1 } = {}) {
    document.querySelectorAll(selector).forEach((el, i) => {
        gsap.fromTo(el, { y, opacity: 0 }, {
            scrollTrigger: { trigger: el, start: 'top 85%', toggleActions: 'play none none none' },
            y: 0, opacity: 1, duration: 0.6, delay: i * stagger, ease: 'power3.out', clearProps: 'all',
        });
    });
}

function initAnimations() {
    gsap.registerPlugin(ScrollTrigger);
    gsap.fromTo('.navbar', { y: -100, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: 'power3.out', clearProps: 'all' });
    reveal('.feature-card, .section-header');
    reveal('.book-card', { y: 40 });
    reveal('.cta', { y: 50 });
    gsap.from('.login-card, .signup-card', { scale: 0.9, opacity: 0, y: 30, duration: 0.8, ease: 'back.out', clearProps: 'all' });
    gsap.from('.form-group', { x: -20, opacity: 0, duration: 0.5, stagger: 0.1, delay: 0.1, ease: 'power3.out', clearProps: 'all' });
}

// ── Interactions ──────────────────────────────────────────────────────────────

function initMobileMenu() {
    const toggle = document.querySelector('.mobile-toggle');
    if (!toggle) return;
    toggle.addEventListener('click', () => {
        document.querySelector('.nav-menu').classList.toggle('active');
        toggle.classList.toggle('active');
    });
}

function initPasswordToggles() {
    document.querySelectorAll('.password-toggle').forEach(button => {
        button.addEventListener('click', () => {
            const input = button.closest('.input-wrapper').querySelector('input');
            const show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            button.querySelector('i').className = show ? 'fas fa-eye-slash' : 'fas fa-eye';
        });
    });
}

function initNewsletter() {
    const form = document.querySelector('.newsletter-form');
    if (!form) return;
    form.addEventListener('submit', e => {
        e.preventDefault();
        form.reset();
        showNotification('Newsletter subscription coming soon!');
    });
}

// ── Login / signup ────────────────────────────────────────────────────────────

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Returns an error message for an invalid field, or '' when it is valid. */
function fieldError(input) {
    switch (input.id) {
        case 'fullName': return input.value.trim().length >= 2 ? '' : 'Full name must be at least 2 characters';
        case 'email': return EMAIL_PATTERN.test(input.value) ? '' : 'Please enter a valid email address';
        case 'password': return input.value.length >= 8 ? '' : 'Password must be at least 8 characters';
        case 'confirmPassword': return input.value === document.getElementById('password').value ? '' : 'Passwords do not match';
        case 'agreeTerms': return input.checked ? '' : 'You must agree to the terms and conditions';
        default: return '';
    }
}

function validateField(input) {
    const message = fieldError(input);
    const output = document.getElementById(input.id === 'agreeTerms' ? 'termsError' : input.id + 'Error');
    if (output) {
        output.textContent = message;
        output.classList.toggle('show', Boolean(message));
    }
    return !message;
}

function initAuthForms() {
    const forms = [
        ['loginForm', '.btn-login', ({ email, password }) => api.login(email.value, password.value).then(data => {
            localStorage.setItem('access_token', data.access_token);
            showNotification('Login successful! Redirecting...');
            setTimeout(() => { window.location.href = 'profile.html'; }, 1000);
        })],
        ['signupForm', '.btn-signup', ({ fullName, email, password }) => api.signup(fullName.value.trim(), email.value, password.value).then(() => {
            showNotification('Account created! Redirecting to login...');
            setTimeout(() => { window.location.href = 'login.html'; }, 1500);
        })],
    ];

    for (const [formId, buttonSelector, submit] of forms) {
        const form = document.getElementById(formId);
        if (!form) continue;
        const inputs = [...form.querySelectorAll('input[required]')];
        inputs.forEach(input => input.addEventListener('input', () => validateField(input)));

        form.addEventListener('submit', async e => {
            e.preventDefault();
            if (!inputs.map(validateField).every(Boolean)) return;

            const button = form.querySelector(buttonSelector);
            const label = button.innerHTML;
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Please wait...';
            try {
                await submit(form.elements);
            } catch (error) {
                button.disabled = false;
                button.innerHTML = label;
                showNotification(error.message, 'error');
            }
        });
    }
}
