document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("change_pswd_btn");
    const pswdForm = document.getElementById("change_pswd_form");
    const oldPswdInput = document.getElementById("input_old_pswd");
    const newPswdInput = document.getElementById("input_new_pswd");

    if (!toggleBtn || !pswdForm) return;

    // Переключение видимости формы
    toggleBtn.addEventListener("click", () => {
        const isHidden = pswdForm.classList.toggle("pswd-form-hidden");

        if (!isHidden) {
            // Если открыли форму — переносим фокус на поле старого пароля
            oldPswdInput.focus();
            toggleBtn.textContent = "Cancel";
        } else {
            // Если закрыли — сбрасываем введенные данные
            oldPswdInput.value = "";
            newPswdInput.value = "";
            toggleBtn.textContent = "Change password";
        }
    });

    // Обработка отправки формы на бэкенд
    pswdForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const payload = {
            old_password: oldPswdInput.value,
            new_password: newPswdInput.value
        };

        try {
            const response = await fetch("/auth/change_password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });


            const data = await response.json();

            if (response.ok && data.ok) {
                // перенаправляем на login
                window.location.href = data.redirect_url || "/login";
            } else {
                // Обработка неверного старого пароля
                oldPswdInput.value = "";
                newPswdInput.value = "";
                alert(data.message || "Ошибка смены пароля");
            }
        } catch (err) {
            console.error("Сетевая ошибка:", err);
        }
    });
});