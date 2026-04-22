from subprocess import run as subprocess_run
from re import search as re_search


print("IP-адрес вида x.x.x.x")
# server_ip = input("Введите ip адрес сервера: ")
default_server_ip = "144.31.134.15"


def ping(server_ip=default_server_ip, packet_size=32, count=4):
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


print(ping())  # пока без параметра сервера, т.к. лень вводить его каждый раз.
# Пинг запихнуть в отдельную функцию которая выводит среднее ms значение, функцию можно касмотризировать.
