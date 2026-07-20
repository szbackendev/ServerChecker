from fastapi import APIRouter, Cookie, Response
from typing import Annotated
from settings import settings
import jwt
import ntplib
import datetime


# возможности админа:
# сброс пароля юзерам(изменение на новый и выдача нового сгенерированного пароля)
# удаление юзеров
# вывод приветственного сообщения "Hello World!"

routeradmin = APIRouter(prefix="/admin_panel", tags=["Admin Functions"])
current_admins = ("admin",)


@routeradmin.get("/message", description="admin access")
def message():
    return {"message": "Hello World!"}


@routeradmin.post(f"/{settings.admin_panel_url}", description="admin access")
def admin_sign_in(
    login: str,
    response: Response,
    access_key,
    auth_cookie: Annotated[str | None, Cookie(alias="Authorization")] = None,
):
    login = login.strip().lower()

    if auth_cookie is None:
        return {"message": "Couldn't access to auth cookie"}

    payload = jwt.decode(
        jwt=auth_cookie,
        key=settings.public_key,
        algorithms=settings.algorithm,
        verify=True,
    )
    is_logged = payload["logged"]
    sub = payload["sub"]

    if (
        is_logged is True
        and access_key == settings.access_key
        and login in current_admins
    ):
        ntplib_client = ntplib.NTPClient()
        ntp_response = ntplib_client.request("pool.ntp.org", version=4)
        # utc_time = datetime.datetime.fromtimestamp(
        #     ntp_response.tx_time, tz=datetime.timezone.utc
        # )
        admin_jwt_token = jwt.encode(
            payload={
                "sub": sub,
                "role": "admin",
                "exp": int(ntp_response.tx_time) + 10800,  # 10.800 секунд это 3 часа
            },
            key=settings.private_key,
            algorithm=settings.algorithm,
        )

        response.set_cookie(
            key="admin_access",
            value=admin_jwt_token,
            httponly=True,
            max_age=10800,  # 10.800 секунд это 3 часа
        )
    else:
        return {"message": "You must login at first."}


def reset_password(user_login: str):
    pass
