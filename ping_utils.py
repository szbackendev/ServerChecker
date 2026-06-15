from subprocess import run as subprocess_run
from ip_handler import ip_choice, funcs
from re import search as re_search

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