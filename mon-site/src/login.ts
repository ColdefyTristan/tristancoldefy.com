const form = document.querySelector<HTMLFormElement>("#login-form");

if (!form) {
    console.warn("login form not found");
} else {
    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const data = new FormData(form);
        const identifier = data.get("identifier");
        const password = data.get("password");

        console.log({ identifier, password });
    });
}