# from re import search as re_search
from re import match as re_match
from ping_utils import manual_ping
from auth import USERS_DB_NAME, settings
import sqlite3
from fastapi import APIRouter, Cookie
import jwt

routerips = APIRouter(prefix="/ips", tags=["IPs"])


DEF_SERVER_IP = "1.1.1.1"
FILE_NAME = "known_IPs.txt"


funcs = {
    1: {"name": "Ручной пинг-чек", "func": manual_ping},
    2: {
        "name": "Не разработанная функция",
        "func": lambda: f"Выбрана еще {funcs[2]['name'].lower()}",
    },
    3: {"name": "Выход", "func": exit},
}


def funcs_choice() -> None:
    while True:
        print(
            f"\nФункционал:\n1. {funcs[1]['name']} сервера\n2. Другие функции будут позже.\n3. {funcs[3]['name']}."
        )
        user_choice = int(
            input(f"Выберите функцию(число[{min(funcs)}-{max(funcs)}]): ")
        )
        if user_choice not in funcs:
            print("\nВведите корректное число")
        elif user_choice == 1:
            ip = ip_choice()
            if ip == "back":
                continue
            else:
                print(funcs[user_choice]["func"](ip))
                break
        else:
            print(funcs[user_choice]["func"]())
            break
    return None


JWT_token = str()


@routerips.get("/get_JWT_token", description="get JWT-token from cookie")
def get_JWT_token(cookies: str = Cookie(default=None, alias="Authorization")):
    global JWT_token
    JWT_token = cookies
    return {"JWT-token": cookies}


def get_user_id():
    # логин по идее должен браться из JWT-токена, который есть в куки

    sub = jwt.decode(
        jwt=JWT_token,
        key=settings.public_key,
        algorithms=settings.algorithm,
        verify=True,
    )["sub"]

    user_id = sub

    if user_id == 0:
        raise ValueError("user_id не найден в БД !")

    return user_id


@routerips.get("/get_ips")
def prev_IPs():  # проверка есть ли таблица known_IPs, если нет то вернуть строку: 'список пред. адресов пуст', если есть то вернуть все 5 ip.

    user_id = get_user_id()

    with sqlite3.connect(USERS_DB_NAME) as users:
        cursor = users.cursor()
        cursor.execute("""SELECT EXISTS (
                       SELECT 1
                       FROM sqlite_master
                       WHERE type = 'table' AND name = 'known_IPs'
                       )""")
        if cursor.fetchone()[0] == 0:
            return {"message": "Список предыдущих IP-адресов пуст."}
        else:
            cursor.execute(
                """SELECT ip FROM known_IPs WHERE user_id = ? ORDER BY id DESC""",
                (user_id,),
            )
            ips = cursor.fetchall()

            if len(ips) == 0:
                return {"message": "Список предыдущих IP-адресов пуст."}
            else:
                list_of_ips = list(ip[0] for ip in ips)
                return {"IPs": list_of_ips}

    # with open(FILE_NAME, mode="a+", encoding="utf-8") as file:
    #     file.seek(0)
    #     strings = file.readlines()
    # if len(strings) == 0:
    #     return "Список предыдущих IP-адресов пуст."
    # else:
    #     return strings[
    #         ::-1
    #     ]  # возвращает список содержащий все строки из файла в обратном порядке(чтоб последний введеный ip был сверху)


def new_IP() -> (
    str
):  # должна возвращать новый IP-адрес и записывать его в known_IPs.txt

    user_id = get_user_id()  # если len(get_users_by_login(rawlogin)) = 1, то там пустой кортеж без инфы о юзере

    if user_id == 0:
        raise ValueError("user_id не найден в БД !")

    while True:
        user_ip = input("Введите IP-адрес: ")
        if re_match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", user_ip):
            break
        else:
            print("\nВведенная строка не является IP-адресом. Формат: X.X.X.X")

    with sqlite3.connect(USERS_DB_NAME) as users:
        cursor = users.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS known_IPs (
                       id INTEGER PRIMARY KEY,
                       user_id INTEGER NOT NULL,
                       ip TEXT NOT NULL,
                       UNIQUE(user_id, ip)
                       )""")

        cursor.execute(
            "INSERT OR IGNORE INTO known_IPs (user_id, ip) VALUES (?,?)",
            (user_id, user_ip),
        )

        cursor.execute("SELECT COUNT(*) FROM known_IPs WHERE user_id = ?", (user_id,))

        if cursor.fetchone()[0] > 5:
            cursor.execute(
                "DELETE FROM known_IPs WHERE user_id = ? AND id = (SELECT MIN(id) FROM known_IPs WHERE user_id = ?)",
                (user_id, user_id),
            )

        users.commit()
    return user_ip
    # with open(FILE_NAME, mode="a+", encoding="utf-8") as file:
    #     file.seek(0)
    #     strings = list()
    #     for string in file.readlines():
    #         strings.append(string.strip("\n"))
    #     ips = list(dict.fromkeys(strings))
    #     if user_ip not in ips:
    #         file.write(f"{user_ip}\n")
    # return user_ip


def prev_IPs_choose_le_5(
    ip_choice_result: list,
) -> (
    int | str | None
):  # отображение списка ip-адресов из файла known_IPs, чтобы пользователь выбрал, но их меньше или равно 5
    for i in range(len(ip_choice_result)):
        print(f"{i + 1}. {ip_choice_result[i].strip()}")
    print("0. Назад")

    user_ip_choice_0_5 = int(input(f"Выберите номер [0-{len(ip_choice_result)}]: "))

    if user_ip_choice_0_5 not in range(0, len(ip_choice_result) + 1):
        print("\nВведите корректное число из списка")
        return 0
    elif user_ip_choice_0_5 == 0:
        return 0
    else:
        return ip_choice_result[user_ip_choice_0_5 - 1].strip()  # возвращаем IP-адрес


def back():
    return "back"


def ip_choice() -> str:  # должен вернуть IP-адрес

    ip_choice_dict = {1: prev_IPs, 2: new_IP, 3: back}

    while True:
        print(
            "\n1. Выбрать из предыдущих IP-адресов\n2. Ввести новый IP-адрес\n3. Назад"
        )
        user_ip_choice = int(
            input(f"Выберите номер [{min(ip_choice_dict)}-{max(ip_choice_dict)}]: ")
        )
        if user_ip_choice not in ip_choice_dict:
            print("Введите корректное число из списка")
        else:
            ip_choice_result = ip_choice_dict[user_ip_choice]()
            if isinstance(ip_choice_result, list):  # если это список с IP-адресами
                # если в списке <= 5 IP-адресов
                print()
                ip_choice_result_0_x = prev_IPs_choose_le_5(ip_choice_result)
                if ip_choice_result_0_x == 0:
                    continue  # возврат к выбору/введению IP-адреса
                else:
                    return str(ip_choice_result_0_x)  # возвращаем IP-адрес
            else:  # если это строка
                if re_match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip_choice_result):
                    return ip_choice_result
                elif (
                    ip_choice_result == "Список предыдущих IP-адресов пуст."
                ):  # если вернулась такая строка от prev_IPs()
                    print("\n", ip_choice_result, sep="")
                    continue
                elif ip_choice_result == "back":
                    return "back"
                else:
                    return "Ошибка1"  # ошибка1 для отладки чтоб понять где упал
