document.addEventListener("DOMContentLoaded", () => {
    const section = document.getElementById("main_content_section_server");
    const ipSelect = document.getElementById("ip_choicer_server");
    
    // Элементы модального окна
    const modal = document.getElementById("modal_add_ip");
    const inputIp = document.getElementById("input_new_ip");
    const btnSaveIp = document.getElementById("btn_save_ip");
    const btnCancelIp = document.getElementById("btn_cancel_ip");
    const ipError = document.getElementById("modal_ip_error");

    // Кнопка из экрана пустого состояния
    const noServersAddBtn = document.getElementById("no_servers_add_btn");

    // Элементы активации службы
    const installBtn = document.getElementById("install_btn_server");
    const alreadyInstalledLink = document.getElementById("undr_btn_text_server");

    let previousSelectedValue = "";
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

    function openAddIpModal() {
        inputIp.value = "";
        ipError.textContent = "";
        modal.classList.remove("modal-hidden");
        inputIp.focus();
    }

    function renderIpOptions(ips, activeIp = null) {
        const addOption = ipSelect.querySelector('option[value="add_new_ip"]');
        ipSelect.innerHTML = "";

        if (!ips || ips.length === 0) {
            // Если серверов 0 — переводим секцию в состояние is-empty
            section.classList.remove("is-inactive");
            section.classList.add("is-empty");

            const emptyOpt = document.createElement("option");
            emptyOpt.value = "";
            emptyOpt.textContent = "No servers added";
            emptyOpt.disabled = true;
            emptyOpt.selected = true;
            ipSelect.appendChild(emptyOpt);
            ipSelect.appendChild(addOption);
            return;
        }

        // Если серверы есть — снимаем состояние пустоты
        section.classList.remove("is-empty");

        ips.forEach((ip, index) => {
            const opt = document.createElement("option");
            opt.value = ip;
            
            // По умолчанию все серверы добавляются со статусом inactive (🔴)
            opt.dataset.status = "inactive";
            opt.textContent = `🔴 | IP: ${ip}`;

            if (activeIp ? ip === activeIp : index === 0) {
                opt.selected = true;
                previousSelectedValue = ip;
            }
            ipSelect.appendChild(opt);
        });

        ipSelect.appendChild(addOption);
        updateInterfaceState();
    }

    function updateInterfaceState() {
        if (section.classList.contains("is-empty")) return;

        const selectedOpt = ipSelect.options[ipSelect.selectedIndex];
        if (!selectedOpt || selectedOpt.value === "add_new_ip" || !selectedOpt.dataset.status) {
            return;
        }

        if (selectedOpt.dataset.status === "inactive") {
            section.classList.add("is-inactive");
        } else {
            section.classList.remove("is-inactive");
        }
    }

    // Перевод выбранного сервера в статус active (🟢)
    function activateCurrentServer() {
        const selectedOpt = ipSelect.options[ipSelect.selectedIndex];
        if (!selectedOpt || selectedOpt.value === "add_new_ip") return;

        selectedOpt.dataset.status = "active";
        selectedOpt.textContent = `🟢 | IP: ${selectedOpt.value}`;
        updateInterfaceState();
    }

    async function loadIps(selectIpAfter = null) {
        try {
            const res = await fetch("/ips/get_ips");
            const data = await res.json();
            if (data.IPs && Array.isArray(data.IPs) && data.IPs.length > 0) {
                renderIpOptions(data.IPs, selectIpAfter);
            } else {
                renderIpOptions([], null);
            }
        } catch (err) {
            console.error("Failed to load IPs:", err);
            renderIpOptions([], null);
        }
    }

    // Слушатели активации службы
    if (installBtn) {
        installBtn.addEventListener("click", activateCurrentServer);
    }
    if (alreadyInstalledLink) {
        alreadyInstalledLink.addEventListener("click", activateCurrentServer);
    }

    // Слушатель выбора в селекторе
    ipSelect.addEventListener("change", () => {
        if (ipSelect.value === "add_new_ip") {
            ipSelect.value = previousSelectedValue;
            openAddIpModal();
        } else {
            previousSelectedValue = ipSelect.value;
            updateInterfaceState();
        }
    });

    // Клик по кнопке на пустом экране
    if (noServersAddBtn) {
        noServersAddBtn.addEventListener("click", openAddIpModal);
    }

    btnCancelIp.addEventListener("click", () => {
        modal.classList.add("modal-hidden");
    });

    btnSaveIp.addEventListener("click", async () => {
        const ipValue = inputIp.value.trim();
        ipError.textContent = "";

        if (!ipRegex.test(ipValue)) {
            ipError.textContent = "Некорректный IPv4 (формат: 192.168.1.1)";
            return;
        }

        try {
            const res = await fetch(`/ips/new_ip?user_ip=${encodeURIComponent(ipValue)}`, {
                method: "POST"
            });
            const result = await res.json();

            if (result.new_ip) {
                modal.classList.add("modal-hidden");
                await loadIps(result.new_ip);
            } else {
                ipError.textContent = result.message || "Ошибка добавления";
            }
        } catch (err) {
            ipError.textContent = "Сетевая ошибка сервера";
        }
    });

    loadIps();
});