import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from admin_panel import routeradmin as adminrouter
from auth import routerauth as authrouter
from ip_handler import routerips as ipsrouter
from webpages import router_pages as pages_router

app = FastAPI()
app.include_router(authrouter)
app.include_router(ipsrouter)
app.include_router(adminrouter)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages_router)

def start():
    uvicorn.run(
        "main:app",
        reload=True,
    )
    # 1. Надо сделать проверку зависимостей из файла requirements.txt


if __name__ == "__main__":
    start()
