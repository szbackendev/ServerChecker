document.addEventListener("DOMContentLoaded", () => {
    const register_form = document.getElementById("register_form");
    const loginInput = document.querySelector('input[name="login_placeholder"]');
    const passwordInput = document.querySelector('input[name="password_placeholder"]');

    if (!register_form) return;

    register_form.addEventListener("submit", async (event) => {
        event.preventDefault();

        // Сбрасываем id к стандартным перед новой отправкой
        resetErrorState();

        const formData = new URLSearchParams(new FormData(register_form));

        try {
            const response = await fetch(register_form.action, {
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
        loginInput.id = "register_login_input_error";
        passwordInput.id = "register_password_input_error";

        // Принудительный перезапуск анимации
        void loginInput.offsetWidth;
        void passwordInput.offsetWidth;

        passwordInput.focus();
    }

    function resetErrorState() {
        loginInput.id = "register_login_input";
        passwordInput.id = "register_password_input";
    }

    // Возвращаем обычный ID при начале нового ввода
    loginInput.addEventListener("input", resetErrorState);
    passwordInput.addEventListener("input", resetErrorState);
});