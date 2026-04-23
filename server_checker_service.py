from platform import freedesktop_os_release as platform_freedesktop_os_release
from subprocess import run as subprocess_run

class server_checker_service:
        def __init__(self):
                pass
        
        def is_alive(self):
                check1 = subprocess_run("systemctl is-system-running", capture_output=True, encoding="utf-8", shell=True).stdout
                if check1.strip() == "running":
                        return True
                else:
                        return False

if platform_freedesktop_os_release()["ID"] in ["debian","ubuntu"]:
        pass
else:
        print("Данный скрипт работает только на Debian/Ubuntu")

checker = server_checker_service()

print(checker.is_alive())
# print(platform.freedesktop_os_release())

# platform.system_alias()
# print(platform.architecture(),platform.machine(),platform.node(),platform.platform(), platform.processor(), platform.python_build(),platform.python_compiler(), platform.python_branch(), platform.python_implementation(), platform.python_revision(), platform.python_version(),platform.release(), platform.system(),platform.version(), platform.uname(),platform.freedesktop_os_release(),sep="\n")
