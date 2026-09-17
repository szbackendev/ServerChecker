import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from admin_panel import routeradmin as adminrouter
from auth import ChangePasswordError, NotAuthenticated, UserNotFoundError
from auth import routerauth as authrouter
from ip_funcs import router_ip_funcs as ip_funcs_router
from ip_handler import ip_handler_error
from ip_handler import routerips as ipsrouter
from lifespan import lifespan
from webpages import router_pages as pages_router

app = FastAPI(lifespan=lifespan)
app.include_router(authrouter)
app.include_router(ip_funcs_router)
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

@app.exception_handler(ip_handler_error)
def ips_error(request: Request, exc: ip_handler_error):
    return JSONResponse(content={"ok": False, "message":"Ошибка в обработчике ip-адресов"}, status_code= 401)
    

def start():
    uvicorn.run(
        "main:app",
        reload=True
    )
   


if __name__ == "__main__":
    start()
