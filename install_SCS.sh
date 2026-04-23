#!/usr/bin/env bash

set -euo pipefail

PROJECT_NAME="ServerChecker"
REPO_URL="https://github.com/f4iny/ServerChecker.git"
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
DATA_FILE="known_IPs.txt"

if [ "${EUID}" -ne 0 ]; then
    echo "Запустите скрипт с правами root: sudo bash install_SCS.sh"
    exit 1
fi

INSTALL_USER="${SUDO_USER:-root}"
if [ "${INSTALL_USER}" = "root" ]; then
    INSTALL_HOME="/root"
else
    INSTALL_HOME="$(getent passwd "${INSTALL_USER}" | cut -d: -f6)"
fi

PROJECT_DIR="${INSTALL_HOME}/${PROJECT_NAME}"

echo "==> Установка будет выполнена для пользователя: ${INSTALL_USER}"
echo "==> Каталог проекта: ${PROJECT_DIR}"

echo "==> Установка системных пакетов для ${PROJECT_NAME}"
apt-get update
apt-get install -y git python3 python3-venv python3-pip

if [ -d "${PROJECT_DIR}" ] && [ ! -d "${PROJECT_DIR}/.git" ]; then
    echo "Каталог ${PROJECT_DIR} уже существует, но не является git-репозиторием."
    echo "Переименуйте или удалите его вручную и запустите установку снова."
    exit 1
fi

if [ ! -d "${PROJECT_DIR}/.git" ]; then
    echo "==> Клонирование репозитория ${REPO_URL}"
    git clone "${REPO_URL}" "${PROJECT_DIR}"
else
    echo "==> Репозиторий уже существует, обновляем"
    git -C "${PROJECT_DIR}" pull --ff-only
fi

cd "${PROJECT_DIR}"

echo "==> Подготовка виртуального окружения"
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo "Виртуальное окружение создано: ${PROJECT_DIR}/${VENV_DIR}"
else
    echo "Виртуальное окружение уже существует: ${PROJECT_DIR}/${VENV_DIR}"
fi

echo "==> Обновление pip"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip

if [ -f "${REQUIREMENTS_FILE}" ]; then
    echo "==> Установка зависимостей из ${REQUIREMENTS_FILE}"
    "${VENV_DIR}/bin/pip" install -r "${REQUIREMENTS_FILE}"
else
    echo "==> ${REQUIREMENTS_FILE} не найден, шаг установки зависимостей пропущен"
fi

if [ ! -f "${DATA_FILE}" ]; then
    echo "==> Создание ${DATA_FILE}"
    touch "${DATA_FILE}"
else
    echo "==> ${DATA_FILE} уже существует"
fi

chown -R "${INSTALL_USER}:${INSTALL_USER}" "${PROJECT_DIR}"

echo
echo "Установка завершена."
echo "Как запускать проект:"
echo "1. cd ${PROJECT_DIR}"
echo "2. source ${VENV_DIR}/bin/activate"
echo "3. python3 main.py"
echo
echo "Без активации окружения можно запускать так:"
echo "${PROJECT_DIR}/${VENV_DIR}/bin/python ${PROJECT_DIR}/main.py"
echo
echo "Команда установки одной строкой:"
echo "sudo bash <(curl -Ls https://raw.githubusercontent.com/f4iny/ServerChecker/refs/heads/main/install_SCS.sh)"
