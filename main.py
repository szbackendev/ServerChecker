import uvicorn
from fastapi import FastAPI
from jinja2 import Environment, FileSystemLoader

from admin_panel import routeradmin as adminrouter
from auth import routerauth as authrouter
from ip_handler import routerips as ipsrouter

app = FastAPI()
app.include_router(authrouter)
app.include_router(ipsrouter)
app.include_router(adminrouter)


# Инициализируем среду с помощью загрузчика каталогов
# Это говорит Jinja2 искать шаблоны в папке templates
env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True
)

def start():
    uvicorn.run(
        "main:app",
        reload=True,
    )
    # 1. Надо сделать проверку зависимостей из файла requirements.txt


if __name__ == "__main__":
    start()
