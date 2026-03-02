async function handleSignup(event) {
    event.preventDefault();
    window.location.href = '/login/';
}

async function handleLogin(event) {
    event.preventDefault();
    window.location.href = '/';
}
