import argon2
import sqlite3
import ntplib
import datetime
# import secrets


USERS_DB_NAME = "users.sqlite3"

# Создаем БД users если еще не создана и суем туда Template
with sqlite3.connect(USERS_DB_NAME) as users:
    cursor = users.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                   id INTEGER PRIMARY KEY,
                   login TEXT NOT NULL UNIQUE,
                   password_hash TEXT NOT NULL,
                   role TEXT NOT NULL,
                   session_token TEXT,
                   session_token_expiration_date TEXT,
                   reg_date TEXT NOT NULL,
                   comment TEXT
                   )""")

    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Users (login, password_hash, role, session_token, session_token_expiration_date, reg_date, comment) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "login0",
                "password_hash0",
                "user",
                "session_token0",
                "yyyy-mm-dd",
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


def sign_in():

    def login_check(login: str, data: tuple) -> bool:
        login = login.strip().lower()
        if login == "login0":  # шо бы не регались под логином с примера
            return False
        elif len(data) > 1 and data[1] == login:
            return True
        return False

    def password_check(password_hash: str, try_count: int = 3) -> bool:
        ph = argon2.PasswordHasher()
        for _ in range(try_count):
            password = input("Введите пароль: ")
            try:
                if ph.verify(password_hash, password):
                    return True
            except argon2.exceptions.VerificationError:
                print("Неверный пароль или что-то сломалось. Повторите попытку.")
            except argon2.exceptions.InvalidHashError:
                print("Проблема с хэшем. Возможно запись в БД повреждена.")
        return False

    while True:
        global login
        login = input("Введите логин: ")
        data = get_users_by_login(login)

        if login_check(login, data) and password_check(
            data[2], try_count=3
        ):  # data[2] это индекс в кортеже где находится хэш пароля
            # session_token = secrets.token_hex(64)
            # data[user_id]["session_token"] = session_token
            # data[user_id]["session_token_expiration_date"] = current_date + "7d"
            # сделать выдачу временного session_token
            return True
        else:
            print(
                "Неправильный логин и/или пароль.\n1. Повторить попытку.\n2. Зарегистрироваться."
            )
            user_choice = int(input("Выберите вариант [1-2]: "))
            if user_choice == 1:
                continue
            else:
                break
    return False  # ведем на регистрацию, где логин будет .lower().strip()


def sign_up():
    print("\nРегистрация:")

    def is_login_available(login) -> bool:
        data = get_users_by_login(login)
        if len(data) > 1:
            return False
        return True

    while True:
        global login
        login = input("Введите желаемый логин: ")
        if is_login_available(login):
            ntplib_client = ntplib.NTPClient()
            response = ntplib_client.request("ru.pool.ntp.org", version=4)
            utc_time = datetime.datetime.fromtimestamp(
                response.tx_time, tz=datetime.timezone.utc
            )

            with sqlite3.connect(USERS_DB_NAME) as users:
                password = input("Введите желаемый пароль: ")
                cursor = users.cursor()
                cursor.execute(
                    "INSERT INTO Users (login, password_hash, role, session_token, session_token_expiration_date, reg_date, comment) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        login,
                        argon2.PasswordHasher().hash(password),
                        "user",
                        None,
                        None,
                        str(utc_time)[:11],  # дата регистрации в формате yyyy-mm-dd
                        None,
                    ),
                )
                users.commit()
            return True

        else:
            print("Указаный логин занят.")
            continue

    # Пароль и сохранение его в хэше в users.json в словарик [login]["password_hash"]
    # Также выдача временного session_token и много еще чего.


def reset_password():
    pass  # доделать функцию сброса пароля
