document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login_form");
    const loginInput = document.querySelector('input[name="login_placeholder"]');
    const passwordInput = document.querySelector('input[name="password_placeholder"]');

    if (!loginForm) return;

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        // Сбрасываем id к стандартным перед новой отправкой
        resetErrorState();

        const formData = new URLSearchParams(new FormData(loginForm));

        try {
            const response = await fetch(loginForm.action, {
                method: "POST",
                body: formData,
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            });

            const data = await response.json();

            if (response.ok && data.ok) {
                window.location.href = data.redirect_url;
            } else {
                applyErrorState();
            }
        } catch (err) {
            applyErrorState();
        }
    });

    function applyErrorState() {
        passwordInput.value = "";

        // Присваиваем ID, отвечающие за ошибку и тряску
        loginInput.id = "login_input_error";
        passwordInput.id = "password_input_error";

        // Принудительный перезапуск анимации
        void loginInput.offsetWidth;
        void passwordInput.offsetWidth;

        passwordInput.focus();
    }

    function resetErrorState() {
        loginInput.id = "login_input";
        passwordInput.id = "password_input";
    }

    // Возвращаем обычный ID при начале нового ввода
    loginInput.addEventListener("input", resetErrorState);
    passwordInput.addEventListener("input", resetErrorState);
});