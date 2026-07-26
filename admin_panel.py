import datetime
import secrets
import sqlite3
import string
from typing import Annotated

import argon2
import jwt
import ntplib
from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel, Field

from auth import get_users_by_login
from settings import settings

# import datetime


# возможности админа:
# сброс пароля юзерам(изменение на новый и выдача нового сгенерированного пароля)
# удаление юзеров
# вывод приветственного сообщения "Hello World!"

routeradmin = APIRouter(prefix=f"/{settings.admin_panel_url}", tags=["Admin Functions"])
USERS_DB_NAME = settings.USERS_DB_NAME
current_admins = {"2": "admin"}  # id: login


class AdminLoginSchema(BaseModel):
    access_key: str


class UserDataSchema(BaseModel):
    user_login: str


class NTP_Server_Schema(BaseModel):
    ntp_pool: str = Field(
        default="ru.pool.ntp.org", pattern=r"\S*.?pool\.ntp\.org$"
    )  # сделать валидацию по формату pool.ntp.org и/или *.pool.ntp.org


class AdminCookieCheck:
    def __init__(self) -> None:
        pass

    def get_tx_time(self, ntp_url: NTP_Server_Schema | None = None):
        if ntp_url is None:
            tx_time = ntplib.NTPClient().request(host="pool.ntp.org", version=4).tx_time
        else:
            tx_time = (
                ntplib.NTPClient().request(host=ntp_url.ntp_pool, version=4).tx_time
            )

        return tx_time

    def boolean(
        self,
        admin_auth_cookie: Annotated[str | None, Cookie(alias="admin_access")] = None,
    ):
        if admin_auth_cookie is None:
            return False

        payload = jwt.decode(
            jwt=admin_auth_cookie,
            key=settings.public_key,
            algorithms=settings.algorithm,
            verify=True,
        )

        try:
            tx_time = int(self.get_tx_time())
        except ntplib.NTPException:
            return False

        return bool(payload["role"] == "admin" and payload["sub"] in current_admins and payload["exp"] > tx_time)

    def detailed(self, admin_auth_cookie) -> dict:

        if admin_auth_cookie is None:
            return {"Error": True}

        payload = jwt.decode(
            jwt=admin_auth_cookie,
            key=settings.public_key,
            algorithms=settings.algorithm,
            verify=True,
        )

        try:
            tx_time = int(self.get_tx_time())
        except ntplib.NTPException:
            return {"Error": True, "message": "Error connecting to pool.ntp.org server"}

        if (
            payload["role"] == "admin"
            and payload["sub"] in current_admins
            and payload["exp"] > tx_time
        ):
            return {
                "Error": False,
                "role": payload["role"],
                "sub": payload["sub"],
                "exp": payload["exp"],
                "is_expired": False,
                "is_sub_in_admins": True,
            }
        else:
            return {"Error": False}


ACC = AdminCookieCheck()


@routeradmin.get("/message", description="admin access")
def message(
    admin_auth_cookie: Annotated[str | None, Cookie(alias="admin_access")] = None,
):
    if ACC.boolean(admin_auth_cookie):
        return {"message": "Hello World!"}
    else:
        return {"message": "Access denied."}


@routeradmin.post("/sign_in", description="admin access")
def admin_sign_in(
    response: Response,
    admin_data: AdminLoginSchema,
    auth_cookie: Annotated[str | None, Cookie(alias="Authorization")] = None,
):

    if auth_cookie is None:
        return {"message": "Couldn't get access to auth cookie"}

    payload = jwt.decode(
        jwt=auth_cookie,
        key=settings.public_key,
        algorithms=settings.algorithm,
        verify=True,
    )

    try:
        is_logged = payload["logged"]
        sub = str(payload["sub"])

        login = (
            current_admins[sub].strip().lower()
        )  # может выбить ошибку если такого sub нет в словаре.
    except KeyError:
        return {"message": "Access denied."}

    if (
        is_logged is True
        and admin_data.access_key == settings.access_key
        and login in current_admins.values()
    ):
        # utc_time = datetime.datetime.fromtimestamp(
        #     ntp_response.tx_time, tz=datetime.timezone.utc
        # )
        admin_jwt_token = jwt.encode(
            payload={
                "sub": str(sub),
                "role": "admin",
                "exp": int(ACC.get_tx_time()) + 10800,  # 10.800 секунд это 3 часа
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

        return {"message": "Access granted."}
    else:
        return {"message": "Access denied."}


@routeradmin.put("/user_reset_password")
def user_reset_password(
    userdata: UserDataSchema,
    admin_auth_cookie: Annotated[str | None, Cookie(alias="admin_access")] = None,
):

    def generate_password(
        length: int | None = None,
        uppercase: bool = True,
        lowercase: bool = True,
        digits: bool = True,
        chars: bool = True,
        use_ambiguous_characters: bool = True,
    ):

        if length is None:
            length = secrets.choice(
                range(16, 25)
            )  # выбираем рандомную длину с 16 по 24

        new_password = ""
        text = ""
        ambiguous_characters = "il1Lo0O"

        if uppercase:
            text += string.ascii_uppercase
        if lowercase:
            text += string.ascii_lowercase
        if digits:
            text += string.digits
        if chars:
            text += string.punctuation

        if len(text) < 9:
            return {"message": "not enough characters"}
        else:
            if use_ambiguous_characters:
                for _ in range(length):
                    new_password += secrets.choice(text)
            else:
                for _ in range(length):
                    c = secrets.choice(text)
                    if c not in ambiguous_characters:
                        new_password += c
                    else:
                        while c in ambiguous_characters:
                            c = secrets.choice(text)
                        new_password += c
            return new_password

    user_login = userdata.user_login

    user = get_users_by_login(user_login)

    if user == (0,):
        return {"message": "User with that login doesn't exist."}
    else:
        if ACC.boolean(admin_auth_cookie):
            new_password = generate_password()

            if type(new_password) is str:
                try:
                    current_time = ACC.get_tx_time()
                except ntplib.NTPException:
                    return {"message": "Error connecting to pool.ntp.org server"}

                with sqlite3.connect(USERS_DB_NAME) as users:
                    cursor = users.cursor()
                    cursor.execute(
                        "UPDATE Users SET password_hash = ?, comment = ? WHERE login = ?",
                        (
                            argon2.PasswordHasher().hash(new_password),
                            f"Password changed at {datetime.datetime.fromtimestamp(current_time, tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')} by {ACC.detailed(admin_auth_cookie)['sub']}",
                            user[1],
                        ),
                    )

                    users.commit()
                return {
                    "message": "Password changed to new",
                    "new_password": new_password,
                }
            else:
                return {"message": "Error generating a new password"}
        else:
            return {"message": "Error with checking admin rights"}


@routeradmin.get("/get_all_users")
def get_all_users(
    admin_auth_cookie: Annotated[str | None, Cookie(alias="admin_access")] = None,
) -> list | bool:
    if ACC.boolean(admin_auth_cookie):
        with sqlite3.connect(USERS_DB_NAME) as users:
            cursor = users.cursor()

            cursor.execute("SELECT * FROM Users")

            all_users = cursor.fetchall()

            return all_users
    else:
        return False


@routeradmin.delete("/delete_user")
def delete_user(
    userdata: UserDataSchema,
    admin_auth_cookie: Annotated[str | None, Cookie(alias="admin_access")] = None,
):
    if ACC.boolean(admin_auth_cookie):
        with sqlite3.connect(USERS_DB_NAME) as users:
            cursor = users.cursor()

            cursor.execute("DELETE FROM Users WHERE login = ?", (userdata.user_login,))

            users.commit()
        return {
            "message": f"user with login '{userdata.user_login}' successfuly deleted"
        }
    else:
        return {"message": "Error"}
