import argon2
import sqlite3
import ntplib
import datetime
from fastapi import APIRouter
from pydantic_settings import BaseSettings, SettingsConfigDict
import jwt
# import secrets

router = APIRouter(prefix="/auth", tags=["Auth"])

USERS_DB_NAME = "users.sqlite3"

# Создаем БД users если еще не создана и суем туда Template
with sqlite3.connect(USERS_DB_NAME) as users:
    cursor = users.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                   id INTEGER PRIMARY KEY,
                   login TEXT NOT NULL UNIQUE,
                   password_hash TEXT NOT NULL,
                   role TEXT NOT NULL,
                   reg_date TEXT NOT NULL,
                   comment TEXT
                   )""")

    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Users (login, password_hash, role, reg_date, comment) VALUES (?, ?, ?, ?, ?)",
            (
                "login0",
                "password_hash0",
                "user",
                "yyyy-mm-dd",
                "Template",
            ),
        )
    users.commit()


def get_users_by_login(login: str) -> tuple:
    with sqlite3.connect(USERS_DB_NAME) as users:
        cursor = users.cursor()
        cursor.execute("SELECT * FROM Users WHERE login = ?", (login.strip().lower(),))
        result = cursor.fetchone()
        if result is not None:
            return result
        else:
            return (0,)


class Settings(BaseSettings):
    TESTMESSAGE: str
    private_key: str
    public_key: str
    algorithm: str

    model_config = SettingsConfigDict(
        env_file="somedata.env",  # если другое название файла окружения, то изменить somedata.env на ваше имяфайла.env
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore

ntplib_client = ntplib.NTPClient()


@router.put("/sign_in")
def sign_in(login: str, password: str):

    def login_check(login: str, data: tuple) -> bool:
        login = login.strip().lower()
        if login == "login0":  # шо бы не регались под логином с примера
            return False
        elif len(data) > 1 and data[1] == login:
            return True
        return False

    def password_check(
        password: str, password_hash: str, try_count: int = 3
    ) -> dict | bool:
        ph = argon2.PasswordHasher()
        for _ in range(try_count):
            try:
                if ph.verify(password_hash, password):
                    return True
            except argon2.exceptions.VerificationError:  # для тестов функции
                return {
                    "message": "Неверный пароль или что-то сломалось. Повторите попытку.",
                    "type": "Error",
                }
            except argon2.exceptions.InvalidHashError:  # для тестов функции
                return {
                    "message": "Проблема с хэшем. Возможно запись в БД повреждена.",
                    "type": "Error",
                }
        return False

    data = get_users_by_login(login)

    if (
        login_check(login, data)
        and password_check(password, data[2], try_count=3) is True
    ):  # data[2] это индекс в кортеже где находится хэш пароля
        response = ntplib_client.request("pool.ntp.org", version=4)

        JWT_token = jwt.encode(
            {
                "payload": {
                    "login": login,
                    "role": "user",
                    "exp": str(
                        datetime.datetime.fromtimestamp(
                            response.tx_time
                            + 86400,  # 86400 секунд это +1 день (жизнь токена 24 часа)
                            tz=datetime.timezone.utc,
                        )
                    ),
                }
            },
            settings.private_key,
            settings.algorithm,
        )  # settings.private_key это приватный ключ, JWT-токен обычно живет 15-60 минут, но для упрощения на данный момент сделаем 24 часа, позже вернем на 15 мин и сделаю refresh token.
        # settings.algorithm это алгоритм кодирования записанный в .env файле

        return {
            "message": "Успешный вход",
            "Authorization": f"Bearer {JWT_token}",
            "bool": True,
        }
    else:
        return {
            "message": "Неправильный логин и/или пароль.\n1. Повторить попытку.\n2. Зарегистрироваться.",
            "bool": False,
        }  # ведем на регистрацию, где логин будет .lower().strip()


@router.put("/sign_up")
def sign_up(login: str, password: str):

    def is_login_available(login) -> bool:
        data = get_users_by_login(login)
        if len(data) > 1:
            return False
        return True

    if is_login_available(login):
        response = ntplib_client.request("pool.ntp.org", version=4)
        utc_time = datetime.datetime.fromtimestamp(
            response.tx_time, tz=datetime.timezone.utc
        )

        with sqlite3.connect(USERS_DB_NAME) as users:
            cursor = users.cursor()
            cursor.execute(
                "INSERT INTO Users (login, password_hash, role, reg_date, comment) VALUES (?, ?, ?, ?, ?)",
                (
                    login,
                    argon2.PasswordHasher().hash(password),
                    "user",
                    str(utc_time)[:11],  # дата регистрации в формате yyyy-mm-dd
                    None,
                ),
            )
            users.commit()

        JWT_token = jwt.encode(
            {
                "payload": {
                    "login": login,
                    "role": "user",
                    "exp": str(
                        datetime.datetime.fromtimestamp(
                            response.tx_time
                            + 86400,  # 86400 секунд это +1 день (жизнь токена 24 часа)
                            tz=datetime.timezone.utc,
                        )
                    ),
                }
            },
            settings.private_key,
            settings.algorithm,
        )  # settings.private_key это приватный ключ, JWT-токен обычно живет 15-60 минут, но для упрощения на данный момент сделаем 24 часа, позже вернем на 15 мин и сделаю refresh token.
        # settings.algorithm это алгоритм кодирования записанный в .env файле

        return {
            "message": "Успешная регистрация",
            "Authorization": f"Bearer {JWT_token}",
            "bool": True,
        }
    else:
        return {"message": "Логин занят", "bool": False}


def reset_password():
    pass  # доделать функцию сброса пароля
