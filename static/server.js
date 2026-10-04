document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // 1. Селекторы элементов интерфейса
    // -------------------------------------------------------------
    const section = document.getElementById("main_content_section_server");
    const ipSelect = document.getElementById("ip_choicer_server");
    
    // Модальное окно добавления IP
    const modal = document.getElementById("modal_add_ip");
    const inputIp = document.getElementById("input_new_ip");
    const btnSaveIp = document.getElementById("btn_save_ip");
    const btnCancelIp = document.getElementById("btn_cancel_ip");
    const ipError = document.getElementById("modal_ip_error");
    const noServersAddBtn = document.getElementById("no_servers_add_btn");

    // Элементы службы
    const installBtn = document.getElementById("install_btn_server");
    const alreadyInstalledLink = document.getElementById("undr_btn_text_server");

    // Блок даты окончания аренды
    const expDiv = document.getElementById("exp_date_func_div_server");
    const expBtn = document.getElementById("exp_date_save_btn");
    const expInfoText = document.getElementById("exp_date_info_texts");
    const inputDay = document.getElementById("exp_date_input_day");
    const inputMonth = document.getElementById("exp_date_input_month");
    const inputYear = document.getElementById("exp_date_input_year");

    // Блок пинга
    const pingSettingsBtn = document.getElementById("ping_settings_btn");
    const pingDateChoicerBtn = document.getElementById("ping_date_choicer_btn");
    const pingSummText = document.getElementById("ping_summ_info_text");
    const pingConfirmDenyBtns = document.getElementById("ping_confirm_deny_btns");
    const pingConfirmBtn = document.getElementById("ping_confirm_btn");
    const pingDenyBtn = document.getElementById("ping_deny_btn");
    const pingManualBtn = document.getElementById("ping_btn");
    
    // Модальное окно метрик пинга
    const pingSettingsPopover = document.getElementById("ping_settings_popover");
    const btnCancelPingSettings = document.getElementById("btn_cancel_ping_settings");
    const btnSavePingSettings = document.getElementById("btn_save_ping_settings");
    
    // Поповер расписания пинга
    const pingSchedulePopover = document.getElementById("ping_schedule_popover");
    const btnCancelPingSchedule = document.getElementById("btn_cancel_ping_schedule");
    const btnSavePingSchedule = document.getElementById("btn_save_ping_schedule");
    const schRadioButtons = document.querySelectorAll('input[name="ping_sch_mode"]');
    const schSubOnce = document.getElementById("sch_sub_once");
    const schSubInterval = document.getElementById("sch_sub_interval");
    const pingScheduleInput = document.getElementById("ping_schedule_input");
    const pingTzHint = document.getElementById("ping_tz_hint");
    const intervalValueInput = document.getElementById("ping_interval_value");
    const intervalUnitSelect = document.getElementById("ping_interval_unit");

    // -------------------------------------------------------------
    // 2. Локальное состояние и кэш
    // -------------------------------------------------------------
    let previousSelectedValue = "";
    const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    
    // Кэш дат окончания аренды: { "192.168.1.1": Date }
    const leaseDatesCache = {};

    const currentPingConfig = {
        metrics: {
            latency: true,
            cpu: true,
            ram: true,
            rom: false,
            services: false
        },
        schedule: {
            mode: "manual", // 'manual' | 'once' | 'interval'
            datetimeLocal: "",
            intervalVal: 15,
            intervalUnit: "min"
        }
    };

    // -------------------------------------------------------------
    // 3. Вспомогательные функции форматирования дат
    // -------------------------------------------------------------
    function formatDateToDisplay(dateObj) {
        if (!dateObj || !(dateObj instanceof Date) || isNaN(dateObj.getTime())) return "";
        const d = String(dateObj.getDate()).padStart(2, "0");
        const m = String(dateObj.getMonth() + 1).padStart(2, "0");
        const y = dateObj.getFullYear();
        return `${d}/${m}/${y}`;
    }

    function formatDateTimeObjToDisplay(dateObj) {
        if (!dateObj || !(dateObj instanceof Date) || isNaN(dateObj.getTime())) return "";
        const pad = (n) => String(n).padStart(2, "0");
        return `${pad(dateObj.getDate())}/${pad(dateObj.getMonth() + 1)}/${dateObj.getFullYear()} ${pad(dateObj.getHours())}:${pad(dateObj.getMinutes())}`;
    }

    function formatDateTimeToDisplay(dtString) {
        if (!dtString) return "";
        const [datePart, timePart] = dtString.split("T");
        if (!datePart) return dtString;
        const [year, month, day] = datePart.split("-");
        if (day && month && year) {
            return timePart ? `${day}/${month}/${year} ${timePart}` : `${day}/${month}/${year}`;
        }
        return dtString;
    }

    function parseIsoDateToDisplay(isoStr) {
        if (!isoStr) return "";
        const parts = isoStr.split("T")[0].split("-");
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        return isoStr;
    }

    // -------------------------------------------------------------
    // 4. Маска ввода даты: ДД/ММ/ГГГГ ЧЧ:ММ
    // -------------------------------------------------------------
    if (pingScheduleInput) {
        pingScheduleInput.addEventListener("input", () => {
            let digits = pingScheduleInput.value.replace(/\D/g, "").slice(0, 12);
            let formatted = "";

            if (digits.length > 0) formatted += digits.substring(0, 2);
            if (digits.length > 2) formatted += "/" + digits.substring(2, 4);
            if (digits.length > 4) formatted += "/" + digits.substring(4, 8);
            if (digits.length > 8) formatted += " " + digits.substring(8, 10);
            if (digits.length > 10) formatted += ":" + digits.substring(10, 12);

            pingScheduleInput.value = formatted;
        });
    }

    // -------------------------------------------------------------
    // 5. Проверка статуса сервера через API (/ips/status?ip=X)
    // -------------------------------------------------------------
    function setServerStatusUI(optionElement, ip, isOnline) {
        optionElement.dataset.status = isOnline ? "active" : "inactive";
        optionElement.textContent = `${isOnline ? "🟢" : "🔴"} | IP: ${ip}`;

        // Если обновляемый сервер сейчас выбран в селекторе — переключаем видимость экранов
        if (ipSelect.value === ip) {
            if (isOnline) {
                section.classList.remove("is-inactive");
            } else {
                section.classList.add("is-inactive");
            }
        }
    }

    async function checkServerStatus(ip) {
        if (!ip || ip === "add_new_ip") return false;

        const targetOpt = Array.from(ipSelect.options).find(opt => opt.value === ip);
        if (!targetOpt) return false;

        try {
            const res = await fetch(`/ips/status?ip=${encodeURIComponent(ip)}`);
            if (!res.ok) {
                // Если ручка еще не готова на бэкенде (404/500) — считаем неактивным
                setServerStatusUI(targetOpt, ip, false);
                return false;
            }
            const data = await res.json();
            // Поддержка как чистого bool (true/false), так и объекта { status: true/false }
            const isOnline = typeof data === "boolean" ? data : Boolean(data === true || data?.status === true);

            setServerStatusUI(targetOpt, ip, isOnline);
            return isOnline;
        } catch (err) {
            // При ошибке соединения или парсинга не роняем скрипт
            setServerStatusUI(targetOpt, ip, false);
            return false;
        }
    }

    // -------------------------------------------------------------
    // 6. Управление списком серверов и модалкой IP
    // -------------------------------------------------------------
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

        section.classList.remove("is-empty");

        ips.forEach((ip) => {
            const opt = document.createElement("option");
            opt.value = ip;
            opt.dataset.status = "inactive";
            opt.textContent = `🔴 | IP: ${ip}`;

            if (activeIp && ip === activeIp) {
                opt.selected = true;
                previousSelectedValue = ip;
            }
            ipSelect.appendChild(opt);
        });

        ipSelect.appendChild(addOption);

        if (!activeIp) {
            addOption.selected = true;
            previousSelectedValue = "add_new_ip";
        }

        updateInterfaceState();
    }

    function updateInterfaceState() {
        if (section.classList.contains("is-empty")) return;

        const selectedOpt = ipSelect.options[ipSelect.selectedIndex];

        if (!selectedOpt || selectedOpt.value === "add_new_ip" || !selectedOpt.dataset.status) {
            section.classList.add("is-inactive");
            return;
        }

        if (selectedOpt.dataset.status === "inactive") {
            section.classList.add("is-inactive");
        } else {
            section.classList.remove("is-inactive");
        }
    }

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
                // Если выбран конкретный IP при загрузке — сразу проверяем статус
                if (selectIpAfter) {
                    await checkServerStatus(selectIpAfter);
                }
            } else {
                renderIpOptions([], null);
            }
        } catch (err) {
            console.error("Failed to load IPs:", err);
            renderIpOptions([], null);
        }
    }

    if (installBtn) installBtn.addEventListener("click", activateCurrentServer);
    
    // Ссылка "Уже установлена?" повторно проверяет ручку /ips/status
    if (alreadyInstalledLink) {
        alreadyInstalledLink.addEventListener("click", () => {
            const currentIp = ipSelect.value;
            if (currentIp && currentIp !== "add_new_ip") {
                checkServerStatus(currentIp);
            }
        });
    }

    function resetPingConfigState() {
        currentPingConfig.metrics = { latency: true, cpu: true, ram: true, rom: false, services: false };
        currentPingConfig.schedule = { mode: "manual", datetimeLocal: "", intervalVal: 15, intervalUnit: "min" };
        pingSummText.textContent = "";
        pingSummText.classList.remove("is-visible");
        pingConfirmDenyBtns.classList.remove("is-visible");
        if (pingScheduleInput) pingScheduleInput.value = "";
        if (pingSettingsPopover) pingSettingsPopover.classList.remove("show");
        if (pingSchedulePopover) pingSchedulePopover.classList.remove("show");
    }

    // Обработчик выбора IP в выпадающем списке
    ipSelect.addEventListener("change", async () => {
        resetExpDateState();
        resetPingConfigState();

        if (ipSelect.value === "add_new_ip") {
            ipSelect.value = previousSelectedValue;
            openAddIpModal();
        } else {
            previousSelectedValue = ipSelect.value;
            updateInterfaceState();
            // Запрос статуса при выборе
            await checkServerStatus(ipSelect.value);
        }
    });

    if (noServersAddBtn) noServersAddBtn.addEventListener("click", openAddIpModal);
    btnCancelIp.addEventListener("click", () => modal.classList.add("modal-hidden"));

    // Добавление нового IP
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
                // Рендерим и сразу опрашиваем добавленный адрес
                await loadIps(result.new_ip);
                await checkServerStatus(result.new_ip);
            } else {
                ipError.textContent = result.message || "Ошибка добавления";
            }
        } catch (err) {
            ipError.textContent = "Сетевая ошибка сервера";
        }
    });

    loadIps();

    // -------------------------------------------------------------
    // 7. Логика блока даты окончания аренды
    // -------------------------------------------------------------
    const dateInputs = [inputDay, inputMonth, inputYear];
    dateInputs.forEach(input => {
        if (!input) return;
        input.addEventListener("input", () => {
            input.value = input.value.replace(/\D/g, "");
        });
    });

    function resetExpDateState() {
        expDiv.classList.remove("is-failed", "is-success");
        expInfoText.textContent = "";
        expInfoText.innerHTML = "";
        if (inputDay) inputDay.value = "";
        if (inputMonth) inputMonth.value = "";
        if (inputYear) inputYear.value = "";
        if (expBtn) expBtn.disabled = false;
    }

    function enableSaveMode() {
        expDiv.classList.remove("is-success");
        expDiv.classList.add("is-failed");
        expInfoText.innerHTML = "Не удалось получить дату с сервера.<br>Укажите её вручную для сохранения.";
    }

    function getCurrentServerLeaseDate(currentIp) {
        if (leaseDatesCache[currentIp]) {
            return leaseDatesCache[currentIp];
        }
        const day = inputDay ? inputDay.value.trim() : "";
        const month = inputMonth ? inputMonth.value.trim() : "";
        const year = inputYear ? inputYear.value.trim() : "";
        if (day && month && year && year.length === 4) {
            const manualDate = new Date(parseInt(year, 10), parseInt(month, 10) - 1, parseInt(day, 10), 23, 59, 59);
            if (!isNaN(manualDate.getTime())) {
                return manualDate;
            }
        }
        return null;
    }

    if (expBtn) {
        expBtn.addEventListener("click", async () => {
            const currentIp = ipSelect.value;
            if (!currentIp || currentIp === "add_new_ip") {
                alert("Пожалуйста, сначала выберите IP-адрес сервера.");
                return;
            }

            const isSaveMode = expDiv.classList.contains("is-failed");

            if (!isSaveMode) {
                expBtn.disabled = true;
                expInfoText.textContent = "Получение данных...";
                expDiv.classList.add("is-success");

                try {
                    const response = await fetch(`/ips/get_lease_date?ip=${encodeURIComponent(currentIp)}`);
                    const result = await response.json();

                    if (response.ok && result.date) {
                        const parsedDate = new Date(result.date + "T23:59:59");
                        if (!isNaN(parsedDate.getTime())) {
                            leaseDatesCache[currentIp] = parsedDate;
                        }
                        expDiv.classList.remove("is-failed");
                        expDiv.classList.add("is-success");
                        expInfoText.textContent = `Дата окончания аренды: ${parseIsoDateToDisplay(result.date)}`;
                    } else {
                        enableSaveMode();
                    }
                } catch (error) {
                    enableSaveMode();
                } finally {
                    expBtn.disabled = false;
                }
            } else {
                const day = inputDay.value.trim().padStart(2, "0");
                const month = inputMonth.value.trim().padStart(2, "0");
                const year = inputYear.value.trim();

                const numDay = parseInt(day, 10);
                const numMonth = parseInt(month, 10);

                if (!numDay || numDay < 1 || numDay > 31 || 
                    !numMonth || numMonth < 1 || numMonth > 12 || 
                    year.length !== 4) {
                    alert("Введите корректную дату: День (1-31), Месяц (1-12), Год (4 цифры).");
                    return;
                }

                expBtn.disabled = true;
                try {
                    const response = await fetch(`/ips/save_lease_date`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            ip: currentIp,
                            expiration_date: `${year}-${month}-${day}`
                        })
                    });

                    if (response.ok) {
                        expDiv.classList.remove("is-failed");
                        expDiv.classList.add("is-success");
                        expInfoText.textContent = `Дата аренды сохранена: ${day}/${month}/${year}`;

                        const manualSavedDate = new Date(parseInt(year, 10), parseInt(month, 10) - 1, parseInt(day, 10), 23, 59, 59);
                        if (!isNaN(manualSavedDate.getTime())) {
                            leaseDatesCache[currentIp] = manualSavedDate;
                        }

                        setTimeout(() => {
                            resetExpDateState();
                        }, 4000);
                    } else {
                        const errData = await response.json();
                        alert(errData.detail || "Не удалось сохранить дату.");
                    }
                } catch (error) {
                    alert("Ошибка соединения с сервером при сохранении даты.");
                } finally {
                    expBtn.disabled = false;
                }
            }
        });
    }

    // -------------------------------------------------------------
    // 8. Логика настроек пинга и расписания
    // -------------------------------------------------------------
    if (pingTzHint) {
        const tzName = Intl.DateTimeFormat().resolvedOptions().timeZone;
        const offsetMin = -new Date().getTimezoneOffset();
        const offsetHours = (offsetMin >= 0 ? "+" : "") + Math.floor(offsetMin / 60);
        pingTzHint.textContent = `Часовой пояс: ${tzName} (UTC${offsetHours}). Сохранение будет в UTC.`;
    }
    
    schRadioButtons.forEach(radio => {
        radio.addEventListener("change", () => {
            schSubOnce.classList.toggle("schedule-block-hidden", radio.value !== "once");
            schSubOnce.classList.toggle("schedule-block-hidden", radio.value !== "once");
            schSubInterval.classList.toggle("schedule-block-hidden", radio.value !== "interval");
            if (pingTzHint) pingTzHint.classList.toggle("schedule-block-hidden", radio.value !== "once");
        });
    });
    
    if (pingSettingsBtn && pingSettingsPopover) {
        pingSettingsBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            if (pingSchedulePopover) pingSchedulePopover.classList.remove("show");
            const isCurrentlyOpen = pingSettingsPopover.classList.contains("show");

            if (!isCurrentlyOpen) {
                // Подгружаем актуальные сохраненные чекбоксы
                document.getElementById("chk_metric_latency").checked = currentPingConfig.metrics.latency;
                document.getElementById("chk_metric_cpu").checked = currentPingConfig.metrics.cpu;
                document.getElementById("chk_metric_ram").checked = currentPingConfig.metrics.ram;
                document.getElementById("chk_metric_rom").checked = currentPingConfig.metrics.rom;
                document.getElementById("chk_metric_services").checked = currentPingConfig.metrics.services;

                pingSettingsPopover.classList.add("show");
            } else {
                pingSettingsPopover.classList.remove("show");
            }
        });
    }
    
    if (pingDateChoicerBtn && pingSchedulePopover) {
        pingDateChoicerBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const isOpen = pingSchedulePopover.classList.contains("show");

            if (isOpen) {
                pingSchedulePopover.classList.remove("show");
                return;
            }

            if (pingSettingsPopover) pingSettingsPopover.classList.remove("show");

            const currentIp = ipSelect.value;
            const now = new Date();

            const oneYearLimit = new Date(now);
            oneYearLimit.setFullYear(oneYearLimit.getFullYear() + 1);
            let effectiveMaxDate = oneYearLimit;
            let limitReason = "максимум 1 год";

            const leaseDate = getCurrentServerLeaseDate(currentIp);
            if (leaseDate && leaseDate instanceof Date && !isNaN(leaseDate.getTime())) {
                if (leaseDate < effectiveMaxDate) {
                    effectiveMaxDate = leaseDate;
                    limitReason = `окончание аренды (${formatDateToDisplay(leaseDate)})`;
                }
            }

            if (pingTzHint) {
                const tzName = Intl.DateTimeFormat().resolvedOptions().timeZone;
                const maxDisplay = formatDateTimeObjToDisplay(effectiveMaxDate);
                pingTzHint.innerHTML = `Часовой пояс: <b>${tzName}</b>.<br>Доступно до: <b>${maxDisplay}</b> [${limitReason}].`;
            }

            const modeRadio = document.querySelector(`input[name="ping_sch_mode"][value="${currentPingConfig.schedule.mode}"]`);
            if (modeRadio) modeRadio.checked = true;

            intervalValueInput.value = currentPingConfig.schedule.intervalVal;
            intervalUnitSelect.value = currentPingConfig.schedule.intervalUnit;

            schSubOnce.classList.toggle("schedule-block-hidden", currentPingConfig.schedule.mode !== "once");
            schSubInterval.classList.toggle("schedule-block-hidden", currentPingConfig.schedule.mode !== "interval");
            schSubOnce.classList.toggle("schedule-block-hidden", currentPingConfig.schedule.mode !== "once");
            schSubInterval.classList.toggle("schedule-block-hidden", currentPingConfig.schedule.mode !== "interval");
            if (pingTzHint) pingTzHint.classList.toggle("schedule-block-hidden", currentPingConfig.schedule.mode !== "once");

            if (currentPingConfig.schedule.datetimeLocal) {
                pingScheduleInput.value = formatDateTimeToDisplay(currentPingConfig.schedule.datetimeLocal);
            } else {
                pingScheduleInput.value = "";
            }

            pingSchedulePopover.classList.add("show");
        });
    }
    
    // 2. Кнопки "Отмена" для обоих поповеров
    if (btnCancelPingSettings && pingSettingsPopover) {
        btnCancelPingSettings.addEventListener("click", () => {
            pingSettingsPopover.classList.remove("show");
        });
    }

    if (btnCancelPingSchedule && pingSchedulePopover) {
        btnCancelPingSchedule.addEventListener("click", () => {
            pingSchedulePopover.classList.remove("show");
        });
    }

    // 3. Кнопка "Применить" для настроек
    if (btnSavePingSettings) {
        btnSavePingSettings.addEventListener("click", () => {
            currentPingConfig.metrics.latency = document.getElementById("chk_metric_latency").checked;
            currentPingConfig.metrics.cpu = document.getElementById("chk_metric_cpu").checked;
            currentPingConfig.metrics.ram = document.getElementById("chk_metric_ram").checked;
            currentPingConfig.metrics.rom = document.getElementById("chk_metric_rom").checked;
            currentPingConfig.metrics.services = document.getElementById("chk_metric_services").checked;

            pingSettingsPopover.classList.remove("show");
            renderPingSummary();
        });
    }

    // 4. Закрытие поповеров при клике в любое свободное место страницы
    document.addEventListener("click", (e) => {
        if (
            pingSettingsPopover &&
            pingSettingsPopover.classList.contains("show") &&
            !pingSettingsPopover.contains(e.target) &&
            pingSettingsBtn &&
            !pingSettingsBtn.contains(e.target)
        ) {
            pingSettingsPopover.classList.remove("show");
        }
        if (
            pingSchedulePopover &&
            pingSchedulePopover.classList.contains("show") &&
            !pingSchedulePopover.contains(e.target) &&
            pingDateChoicerBtn &&
            !pingDateChoicerBtn.contains(e.target)
        ) {
            pingSchedulePopover.classList.remove("show");
        }
    });
    
    if (btnSavePingSchedule) {
        btnSavePingSchedule.addEventListener("click", () => {
            const selectedMode = document.querySelector('input[name="ping_sch_mode"]:checked').value;
            let isoString = "";
        
            if (selectedMode === "once") {
                const val = pingScheduleInput.value.trim();
    
                if (!val) {
                    alert("Пожалуйста, введите дату.");
                    pingScheduleInput.focus();
                    return;
                }
    
                const match = val.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?$/);
                if (!match) {
                    alert("Неверный формат. Введите дату: ДД/ММ/ГГГГ или ДД/ММ/ГГГГ ЧЧ:ММ");
                    pingScheduleInput.focus();
                    return;
                }
    
                const day = parseInt(match[1], 10);
                const month = parseInt(match[2], 10);
                const year = parseInt(match[3], 10);
    
                const hours = match[4] !== undefined ? parseInt(match[4], 10) : 0;
                const mins = match[5] !== undefined ? parseInt(match[5], 10) : 0;
    
                if (month < 1 || month > 12 || hours < 0 || hours > 23 || mins < 0 || mins > 59) {
                    alert("Некорректные значения месяца (1-12), часов (00-23) или минут (00-59).");
                    pingScheduleInput.focus();
                    return;
                }
    
                const targetDate = new Date(year, month - 1, day, hours, mins, 0);
                if (
                    targetDate.getFullYear() !== year ||
                    targetDate.getMonth() !== month - 1 ||
                    targetDate.getDate() !== day
                ) {
                    alert("Такой даты не существует в календаре (проверьте число дней в месяце).");
                    pingScheduleInput.focus();
                    return;
                }
    
                const now = new Date();
                if (targetDate <= now) {
                    alert("Нельзя запланировать действие в прошлом времени.");
                    pingScheduleInput.focus();
                    return;
                }
    
                const currentIp = ipSelect.value;
                const oneYearLimit = new Date(now);
                oneYearLimit.setFullYear(oneYearLimit.getFullYear() + 1);
                let maxLimit = oneYearLimit;
    
                const leaseDate = getCurrentServerLeaseDate(currentIp);
                if (leaseDate && leaseDate instanceof Date && !isNaN(leaseDate.getTime())) {
                    if (leaseDate < maxLimit) {
                        maxLimit = leaseDate;
                    }
                }
    
                if (targetDate > maxLimit) {
                    alert("Выбранная дата превышает допустимый предел (1 год или срок окончания аренды).");
                    pingScheduleInput.focus();
                    return;
                }
    
                const pad = (n) => String(n).padStart(2, "0");
                pingScheduleInput.value = `${pad(day)}/${pad(month)}/${year} ${pad(hours)}:${pad(mins)}`;
                isoString = `${year}-${pad(month)}-${pad(day)}T${pad(hours)}:${pad(mins)}`;
            }
        
            currentPingConfig.schedule.mode = selectedMode;
            currentPingConfig.schedule.datetimeLocal = isoString;
            currentPingConfig.schedule.intervalVal = parseInt(intervalValueInput.value, 10) || 15;
            currentPingConfig.schedule.intervalUnit = intervalUnitSelect.value;
        
            if (pingSchedulePopover) pingSchedulePopover.classList.remove("show");
            renderPingSummary();
        });
    };
    
    function renderPingSummary() {
        const activeMetrics = ["Доступность"];
        if (currentPingConfig.metrics.latency) activeMetrics.push("RTT");
        if (currentPingConfig.metrics.cpu) activeMetrics.push("CPU");
        if (currentPingConfig.metrics.ram) activeMetrics.push("RAM");
        if (currentPingConfig.metrics.rom) activeMetrics.push("ROM");
        if (currentPingConfig.metrics.services) activeMetrics.push("Службы");
    
        let scheduleText = "ручной запуск";
        if (currentPingConfig.schedule.mode === "once") {
            scheduleText = currentPingConfig.schedule.datetimeLocal 
                ? `разово в ${formatDateTimeToDisplay(currentPingConfig.schedule.datetimeLocal)}` 
                : "разово (дата не выбрана)";
        } else if (currentPingConfig.schedule.mode === "interval") {
            const unitsMap = { min: "мин", hour: "ч", day: "дн" };
            scheduleText = `каждые ${currentPingConfig.schedule.intervalVal} ${unitsMap[currentPingConfig.schedule.intervalUnit]}`;
        }
    
        pingSummText.textContent = `Метрики: [${activeMetrics.join(", ")}]. Режим: ${scheduleText}.`;
        pingSummText.classList.add("is-visible");
        pingConfirmDenyBtns.classList.add("is-visible");
    }
    
    if (pingConfirmBtn) {
        pingConfirmBtn.addEventListener("click", () => {
            pingConfirmDenyBtns.classList.remove("is-visible");
            pingSummText.textContent = "✅ Конфигурация пинга зафиксирована.";
            setTimeout(() => {
                pingSummText.classList.remove("is-visible");
                pingSummText.textContent = "";
            }, 2500);
        });
    }
    
    if (pingDenyBtn) {
        pingDenyBtn.addEventListener("click", () => {
            resetPingConfigState();
        });
    }
    
    if (pingManualBtn) {
        pingManualBtn.addEventListener("click", async () => {
            const currentIp = ipSelect.value;
            if (!currentIp || currentIp === "add_new_ip") {
                alert("Пожалуйста, сначала выберите IP-адрес сервера.");
                return;
            }

            // Токен не передаем: кука авторизации уходит автоматически с запросом
            const payload = {
                metrics: currentPingConfig.metrics,
                schedule: currentPingConfig.schedule
            };

            pingManualBtn.disabled = true;

            try {
                const response = await fetch(`/ips/task/ping?ip=${encodeURIComponent(currentIp)}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    pingSummText.textContent = "✅ Задача пинга отправлена на сервер.";
                    pingSummText.classList.add("is-visible");
                    setTimeout(() => {
                        pingSummText.classList.remove("is-visible");
                        pingSummText.textContent = "";
                    }, 3000);
                } else {
                    const errData = await response.json().catch(() => ({}));
                    alert(errData.detail || "Не удалось запустить пинг.");
                }
            } catch (err) {
                console.error("Ошибка при отправке задачи пинга:", err);
                alert("Сетевая ошибка при обращении к серверу.");
            } finally {
                pingManualBtn.disabled = false;
            }
        });
    }
});