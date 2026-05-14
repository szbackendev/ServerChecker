from subprocess import run as subprocess_run
from re import search as re_search, match as re_match
from fastapi import FastAPI
import json
import argon2
import secrets
import datetime

DEF_SERVER_IP = "144.31.134.15"
FILE_NAME = "known_IPs.txt"

app = FastAPI()


@app.get("/")
def main():
    return {"message": "Hello World"}


def ping(server_ip, packet_size=32, count=4) -> str:
    print("\nПингуем...")
    text = subprocess_run(
        f"ping -l {packet_size} -n {count} {server_ip}",
        capture_output=True,
        text=True,
        encoding="cp866",
    ).stdout
    finded_text = re_search(r"Среднее = \d+ мсек", text)
    if finded_text is None:
        raise TypeError("Ошибка в поиске среднего значения")
    else:
        avg = finded_text.group()
        return avg[avg.find("=") + 2 :]


def manual_ping(
    latency=True,
    status=True,
    cpu_load=True,
    ram_load=True,
    disk_space=True,
    enabled_services=True,
    simple_hello=True,
):
    print(f"\nВыбрана функция {funcs[1]['name'].lower()}")
    server_ip = ip_choice()
    if latency:
        print(ping(server_ip))
    if simple_hello:
        pass
    return "Завершение manual_ping функции, IP сервера: " + server_ip


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
        else:
            print(funcs[user_choice]["func"]())
            break
    return None


def prev_IPs() -> str | list:
    with open(FILE_NAME, mode="a+", encoding="utf-8") as file:
        file.seek(0)
        strings = file.readlines()
    if len(strings) == 0:
        return "Список предыдущих IP-адресов пуст."
    else:
        return strings[
            ::-1
        ]  # возвращает список содержащий все строки из файла в обратном порядке(чтоб последний введеный ip был сверху)


def new_IP() -> (
    str
):  # должна возвращать новый IP-адрес и записывать его в known_IPs.txt
    while True:
        user_ip = input("Введите IP-адрес: ")
        if re_match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", user_ip):
            break
        else:
            print("\nВведенная строка не является IP-адресом. Формат: X.X.X.X")
    with open(FILE_NAME, mode="a+", encoding="utf-8") as file:
        file.write(f"{user_ip}\n")
    return user_ip


def prev_IPs_choose_le_5(
    ip_choice_result: list,
) -> (
    int | str | None
):  # отображение списка ip-адресов из файла known_IPs, чтобы пользователь выбрал, но их меньше или равно 5
    for i in range(len(ip_choice_result)):
        print(f"{i + 1}. {ip_choice_result[i].strip()}")
    print("0. Назад")
    user_ip_choice_0_5 = int(input(f"Выберите номер [0-{len(ip_choice_result)}]: "))
    if user_ip_choice_0_5 not in range(0, 6):
        print("Введите корректное число из списка")
    elif user_ip_choice_0_5 == 0:
        return 0
    else:
        return ip_choice_result[user_ip_choice_0_5 - 1].strip()  # возвращаем IP-адрес


def prev_IPs_choose_gt_5(
    ip_choice_result: list,
) -> (
    str | int | None
):  # отображение списка ip-адресов из файла known_IPs, чтобы пользователь выбрал
    print(
        f"\nБудет отображено только последние 5 IP-адресов, остальные хранятся в файле {FILE_NAME}\n"
    )
    for i in range(5):
        print(f"{i + 1}. {ip_choice_result[i].strip()}")
    print("0. Назад")
    user_ip_choice_0_5 = int(input("Выберите номер [0-5]: "))
    if user_ip_choice_0_5 not in range(0, 6):
        print("Введите корректное число из списка")
    elif user_ip_choice_0_5 == 0:
        return 0
    else:
        return ip_choice_result[user_ip_choice_0_5 - 1].strip()  # возвращаем IP-адрес


ip_choice_dict = {1: prev_IPs, 2: new_IP, 3: lambda: funcs_choice()}


def ip_choice() -> str:  # должен вернуть IP-адрес
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
                if len(ip_choice_result) > 5:  # если в списке > 5 IP-адресов
                    user_ip_choice_0_5 = prev_IPs_choose_gt_5(ip_choice_result)
                    if user_ip_choice_0_5 == 0:  # Если выбрали вернуться Назад
                        continue  # возврат к выбору/введению IP-адреса
                    else:
                        return str(user_ip_choice_0_5)
                else:  # если в списке <= 5 IP-адресов
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
                else:
                    return "Ошибка1"

    return "Ошибка2"


# сделать получение даты локально или time.google.com
# def current_date(detailed = False):
#     if detailed:
#         pass
#     else:
#         pass


def get_users() -> dict:
    with open("users.json", mode="a+", encoding="utf-8") as file:
        file.seek(0)
        data = file.readlines()
        if data:
            try:
                file.seek(0)
                data = json.load(file)
                return data
            except:
                raise ValueError("Данные в файле users.json не в формате JSON")
        else:
            template = {
                "id0": {
                    "login": "login0",
                    "password_hash": "password_hash0",
                    "session_token": "session_token0",
                    "session_token_expiration_date": "yyyy-mm-dd",
                    "reg_data": "yyyy-mm-dd",
                    "comment": "Template",
                }
            }
            json.dump(template, file, indent=2)
            raise ValueError(
                "Файл users.json пуст. Записан пример для заполнения файла."
            )


def get_next_id() -> str | None:
    data = get_users()
    for last_id in reversed(data):
        return f"id{int(last_id[last_id.find('id') + 2 :]) + 1}"


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
            with open("users.json", mode="r+", encoding="utf-8") as file:
                password = input("Введите желаемый пароль: ")
                file.seek(0, 2)
                tmp = file.seek(file.tell() - 3) + 3
                file.write(",\n")
                data = {
                    get_next_id(): {
                        "login": login,
                        "password_hash": argon2.PasswordHasher().hash(password),
                        "session_token": None,
                        "session_token_expiration_date": None,
                        "reg_data": str(datetime.date.today()),
                        "comment": None,
                    }
                }
                json.dump(data, file, indent=2)
                file.seek(tmp)
                file.write(" ")
            return True

        else:
            print("Указаный логин занят.")
            continue

    # Пароль и сохранение его в хэше в users.json в словарик [login]["password_hash"]
    # Также выдача временного session_token и много еще чего.


def reset_password():
    pass


def start():
    # 1. Проверка всех зависимостей.
    # 2. Выбор пользователя(регистрация/логин)
    while True:
        user_choice = int(input("1. Вход\n2. Регистрация\nВыберите [1-2]: "))
        if user_choice == 1:
            if sign_in():
                print("Успешный вход.")
                break  # пускаем
            else:
                print("Не удалось войти.")
                continue  # не пускаем
        else:
            if sign_up():
                print("Успешная регистрация.")
                break  # пускаем
            else:
                print("Не удалось зарегистрироваться.")
                continue  # не пускаем
    # 3. ...
    funcs_choice()


if __name__ == "__main__":
    start()
    # sign_in()
    # sign_up()
