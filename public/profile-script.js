/* Profile page: auth guard, account details, activity counts and logout. */

document.addEventListener('DOMContentLoaded', async () => {
    if (!isLoggedIn()) return redirectToLogin();

    document.querySelector('.btn-logout').addEventListener('click', () => {
        localStorage.removeItem('access_token');
        redirectToLogin();
    });

    try {
        const user = await api.getCurrentUser();
        document.querySelector('.profile-name').textContent = user.name;
        document.querySelector('.profile-email').innerHTML = `<i class="fas fa-envelope"></i> ${escapeHtml(user.email)}`;

        const [listed, orders, rentals] = await Promise.all([
            api.getBooks({ sellerId: user.id }),
            api.getOrders(),
            api.getRentals(),
        ]);
        document.getElementById('statListed').textContent = listed.length;
        document.getElementById('statOrders').textContent = orders.length;
        document.getElementById('statRentals').textContent = rentals.length;
    } catch (error) {
        console.error('Profile load error:', error);
    }
});
