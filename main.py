import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from admin_panel import routeradmin as adminrouter
from auth import ChangePasswordError, NotAuthenticated, UserNotFoundError
from auth import routerauth as authrouter
from ip_handler import routerips as ipsrouter
from webpages import router_pages as pages_router

app = FastAPI()
app.include_router(authrouter)
app.include_router(ipsrouter)
app.include_router(adminrouter)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pages_router)

@app.exception_handler(NotAuthenticated)
def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)

@app.exception_handler(UserNotFoundError)
def db_data_error(request: Request, exc: UserNotFoundError):
    return JSONResponse(content={"ok":False, "message":"Неправильный логин и/или пароль"}, status_code=401)

@app.exception_handler(ChangePasswordError)
def identical_pswds(request: Request, exc: ChangePasswordError):
    return JSONResponse(content={"ok": False, "message": "Ошибка в форме сброса пароля от имени пользователя"}, status_code=401)

def start():
    uvicorn.run(
        "main:app",
        reload=True,
    )
    # 1. Надо сделать проверку зависимостей из файла requirements.txt


if __name__ == "__main__":
    start()
