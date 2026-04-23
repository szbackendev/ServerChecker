#!/usr/bin/env bash

set -e

PROJECT_NAME="ServerChecker"
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
DATA_FILE="known_IPs.txt"

if [ "${EUID}" -ne 0 ]; then
    echo "Запустите скрипт с правами root: sudo bash install_SCS.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "==> Установка системных пакетов для ${PROJECT_NAME}"
apt-get update
apt-get install -y python3 python3-venv python3-pip

echo "==> Подготовка виртуального окружения"
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo "Виртуальное окружение создано: ${SCRIPT_DIR}/${VENV_DIR}"
else
    echo "Виртуальное окружение уже существует: ${SCRIPT_DIR}/${VENV_DIR}"
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

echo
echo "Установка завершена."
echo "Как запускать проект:"
echo "1. cd ${SCRIPT_DIR}"
echo "2. source ${VENV_DIR}/bin/activate"
echo "3. python3 main.py"
echo
echo "Без активации окружения можно запускать так:"
echo "${SCRIPT_DIR}/${VENV_DIR}/bin/python ${SCRIPT_DIR}/main.py"
