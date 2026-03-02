const headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : ''
};

// Common Authentication logic
async function handleLogout() {
    window.location.href = '/login/';
}

// Global initialization logic if needed
document.addEventListener('DOMContentLoaded', () => {
    // Shared init
});
