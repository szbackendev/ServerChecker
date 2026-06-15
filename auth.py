import json
import argon2
import secrets
import datetime
import sqlite3


USERS_DB_NAME = "users.sqlite3"

# Создаем БД users если еще не создана и суем туда Template
with sqlite3.connect(USERS_DB_NAME) as users:
    cursor = users.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                   id INTEGER PRIMARY KEY,
                   login TEXT NOT NULL UNIQUE,
                   password_hash TEXT NOT NULL,
                   session_token TEXT,
                   session_token_expiration_date TEXT,
                   reg_date TEXT NOT NULL,
                   comment TEXT
                   )""")
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Users (login, password_hash, session_token, session_token_expiration_date, reg_date, comment) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "login0",
                "password_hash0",
                "session_token0",
                "yyyy-mm-dd",
                "yyyy-mm-dd",
                "Template",
            ),
        )
    users.commit()


def get_users() -> dict:
    with sqlite3.connect(USERS_DB_NAME) as users:
        cursor = users.cursor()
        cursor.execute("SELECT * FROM Users")
        columns = [col[0] for col in cursor.description]
        users_dict = dict()

        for row in cursor.fetchall():
            user_data = dict(zip(columns[1:], row[1:]))
            users_dict[row[0]] = user_data

    return users_dict

    # with open("users.json", mode="a+", encoding="utf-8") as file:
    #     file.seek(0)
    #     data = file.readlines()
    #     if data:
    #         try:
    #             file.seek(0)
    #             data = json.load(file)
    #             return data
    #         except:
    #             raise ValueError("Данные в файле users.json не в формате JSON")
    #     else:
    #         template = {
    #             "id0": {
    #                 "login": "login0",
    #                 "password_hash": "password_hash0",
    #                 "session_token": "session_token0",
    #                 "session_token_expiration_date": "yyyy-mm-dd",
    #                 "reg_data": "yyyy-mm-dd",
    #                 "comment": "Template",
    #             }
    #         }
    #         json.dump(template, file, indent=2)
    #         raise ValueError(
    #             "Файл users.json пуст. Записан пример для заполнения файла."
    #         )


def get_next_id() -> str | None:
    data = get_users()
    for last_id in reversed(data):
        return last_id + 1
        # return f"id{int(last_id[last_id.find('id') + 2 :]) + 1}"


def sign_in():
    data = get_users()
    user_id = str()

    def login_check(login: str, data: dict) -> bool:
        for id, user in data.items():
            if user["login"] == login.lower().strip():
                nonlocal user_id
                user_id = id
                return True
        return False

    def password_check(login: str, data: dict, try_count: int = 3) -> bool:
        ph = argon2.PasswordHasher()
        for _ in range(try_count):
            password = input("Введите пароль: ")
            try:
                if ph.verify(data[user_id]["password_hash"], password):
                    return True
            except:
                print("Неверный пароль или что-то сломалось. Повторите попытку.")
        return False

    while True:
        login = input("Введите логин: ")

        if login_check(login, data) and password_check(login, data, try_count=3):
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
        data = get_users()
        for user in data.values():
            # print(user)
            if user["login"] == login.lower().strip():
                return False
        return True

    while True:
        login = input("Введите желаемый логин: ")
        if is_login_available(login):
            with sqlite3.connect(USERS_DB_NAME) as users:
                password = input("Введите желаемый пароль: ")
                cursor = users.cursor()
                cursor.execute(
                    "INSERT INTO Users (login, password_hash, session_token, session_token_expiration_date, reg_date, comment) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        login,
                        argon2.PasswordHasher().hash(password),
                        None,
                        None,
                        str(datetime.date.today()),
                        None,
                    ),
                )
                users.commit()
            return True

            # with open("users.json", mode="r+", encoding="utf-8") as file:
            #     password = input("Введите желаемый пароль: ")
            #     file.seek(0, 2)
            #     tmp = file.seek(file.tell() - 3) + 3
            #     file.write(",\n")
            #     data = {
            #         get_next_id(): {
            #             "login": login,
            #             "password_hash": argon2.PasswordHasher().hash(password),
            #             "session_token": None,
            #             "session_token_expiration_date": None,
            #             "reg_data": str(datetime.date.today()),
            #             "comment": None,
            #         }
            #     }
            #     json.dump(data, file, indent=2)
            #     file.seek(tmp)
            #     file.write(" ")
            # return True

        else:
            print("Указаный логин занят.")
            continue

    # Пароль и сохранение его в хэше в users.json в словарик [login]["password_hash"]
    # Также выдача временного session_token и много еще чего.


def reset_password():
    pass
