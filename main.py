from subprocess import run as subprocess_run
from re import search as re_search


default_server_ip = "144.31.134.15"


def ping(server_ip=default_server_ip, packet_size=32, count=4) -> str:
    print("Пингуем...")
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


def manual_ping(latency=True):
    print(f"Выбрана функция {funcs[1]['name'].lower()}")
    server_ip = ip_choice()
    return "Завершение manual_ping функции"
    # if latency:
    #     return ping()
    # else:
    #     return ping()


# print("IP-адрес вида x.x.x.x")
# server_ip = input("Введите ip адрес сервера: ")
# Пинг запихнуть в отдельную функцию которая выводит среднее ms значение, функцию можно касмотризировать.




funcs = {
    1: {"name": "Ручной пинг-чек", "func": manual_ping},
    2: {
        "name": "Не разработанная функция",
        "func": lambda: f"Выбрана еще {funcs[2]['name'].lower()}",
    },
    3: {"name": "Выход", "func": exit},
}



def funcs_choice():
    while True:
        print(
            f"\nФункционал:\n1. {funcs[1]['name']} сервера\n2. Другие функции будут позже.\n3. {funcs[3]['name']}."
        )
        user_choice = int(
            input(f"Выберите функцию(число[{min(funcs)}-{max(funcs)}]): ")
        )
        if user_choice not in funcs:
            print("Введите корректное число")
        else:
            print(funcs[user_choice]["func"]())
            break


def prev_IPs():
    with open("known_IPs.txt", mode="r", encoding="utf-8") as file:
        strings = file.readlines()
    if len(strings) == 0:
        return "Список предыдущих IP-адресов пуст."
    else:
        return strings  # возвращает список содержащий все строки из файла
        

def new_IP():  # должна возвращать новый IP-адрес и записывать его в known_IPs.txt сверху
    return "Выбрана функция ввода нового IP-адреса."


ip_choice_dict = {1: prev_IPs, 2: new_IP, 3: lambda: funcs_choice()}


def ip_choice():
    while True:
        print(
            "\nСписок:\n1. Выбрать из предыдущих IP-адресов\n2. Ввести новый IP-адрес\n3. Назад"
        )
        user_ip_choice = int(
            input(f"Выберите из списка[{min(ip_choice_dict)}-{max(ip_choice_dict)}]: ")
        )
        if user_ip_choice not in ip_choice_dict:
            print("Введите корректное число из списка")
        else:
            ip_choice_result = ip_choice_dict[user_ip_choice]()
            if isinstance(ip_choice_result, list):
                if len(ip_choice_result) > 5:
                    while True:
                        print("Будет отображено только 5 IP-адресов, остальные хранятся в файле known_IPs.txt")
                        for i in range(5):
                            print(f"{i+1}. {ip_choice_result[i]}")
                        print("\n0. Назад")
                        user_ip_choice_0_5 = int(input("Выберите номер [0-5]: "))
                        if user_ip_choice_0_5 not in range(0, 6):
                            print("Введите корректное число из списка")
                        else:
                            break
                    if ip_choice_result == 0:
                        continue
                else:
                    while True:
                        for i in range(5):
                            print(f"{i+1}. {ip_choice_result[i]}")
                        print("\n0. Назад")
                        user_ip_choice_0_5 = int(input("Выберите номер [0-5]: "))
                        if user_ip_choice_0_5 not in range(0, 6):
                            print("Введите корректное число из списка")
                        else:
                            break
                    if ip_choice_result == 0:
                        continue 
            else:
                if ip_choice_result  # строка похожа на IP-адрес, то break
                else  # строка не похожа на IP-адрес, то continue
          
        break
    return ip_choice_result[user_ip_choice_0_5 - 1]
            


funcs_choice()
print("\nСкрипт завершил работу.")
