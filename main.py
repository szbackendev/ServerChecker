import uvicorn
from fastapi import FastAPI
from auth import routerauth as authrouter
from ip_handler import routerips as ipsrouter
from admin_panel import routeradmin as adminrouter


app = FastAPI()
app.include_router(authrouter)
app.include_router(ipsrouter)
app.include_router(adminrouter)


def start():
    uvicorn.run(
        "main:app",
        reload=True,
    )
    # 1. Надо сделать проверку зависимостей из файла requirements.txt


if __name__ == "__main__":
    start()
