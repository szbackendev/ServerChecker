from subprocess import run as subprocess_run


print("IP-адрес вида x.x.x.x")
# server_ip = input("Введите ip адрес сервера: ")
server_ip = "144.31.134.15"
default_server_ip = "144.31.134.15"


def ping(server_ip=default_server_ip):
    text = subprocess_run(
        ["ping", server_ip], capture_output=True, text=True, encoding="cp866"
    ).stdout
    return text[text.find("Среднее = ") + 10 :]


print(ping(server_ip))
# Пинг запихнуть в отдельную функцию которая выводит среднее ms значение, функцию можно касмотризировать.
