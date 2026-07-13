from subprocess import run as subprocess_run
import re
#from re import search as re_search


def ping(server_ip, packet_size = 32, count = 4) -> str:
    print("\nПингуем...")
    return_value = float(-1)
    text = subprocess_run(['ping','-s', str(packet_size), '-c', str(count), '-q', server_ip], capture_output = True, text = True, encoding = "UTF-8",).stdout
    '''
    text = subprocess_run(
        f"ping -l {packet_size} -n {count} {server_ip}",
        capture_output = True,
        text = True,
        encoding = "cp866",
    ).stdout

    finded_text = re_search(r"Среднее = \d+ мсек", text)
    if finded_text is None:
        raise TypeError("Ошибка в поиске среднего значения")
    else:
        avg = finded_text.group()
        return avg[avg.find("=") + 2 :]
    '''
    #if re_search(r"Среднее = \\d+ мсек", text)
    pattern = re.compile(r'(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)')
    for _ in text.split('\n'):
        match = pattern.search(_)
        if match:
            return_value = float(match.group(2))
    return return_value

def manual_ping(
    server_ip,
    latency = True,
    status = True,
    cpu_load = True,
    ram_load = True,
    disk_space = True,
    enabled_services = True,
    simple_hello = True,
):
    print("\nВыбрана функция ручной пинг-чек")
    # server_ip = ip_choice()
    if latency:
        print(ping(server_ip))
    if simple_hello:
        pass
    return "Завершение manual_ping функции, IP сервера: " + server_ip
