import datetime
import sqlite3
from typing import Annotated

import argon2
import jwt
import ntplib
from fastapi import APIRouter, Cookie, Depends, Form, Response
from pydantic import BaseModel, Field

from settings import settings

routerauth = APIRouter(prefix="/auth", tags=["Auth"])

USERS_DB_NAME = settings.USERS_DB_NAME

# Создаем БД users если еще не создана и суем туда Template
with sqlite3.connect(USERS_DB_NAME) as users:
    cursor = users.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                   id INTEGER PRIMARY KEY,
                   login TEXT NOT NULL UNIQUE,
                   password_hash TEXT NOT NULL,
                   role TEXT NOT NULL,
                   reg_date TEXT NOT NULL,
                   token_version INTEGER DEFAULT 1,
                   comment TEXT
                   )""")

    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Users (login, password_hash, role, reg_date, token_version, comment) VALUES (?, ?, ?, ?, ?, ?)",
            (
                "login0",
                "password_hash0",
                "user",
                "yyyy-mm-dd",
                "1",
                "Template",
            ),
        )
    users.commit()

class UserNotFoundError(Exception):
    pass


def get_users_by_login(login: str) -> tuple:
    with sqlite3.connect(USERS_DB_NAME) as users:
        cursor = users.cursor()
        cursor.execute("SELECT * FROM Users WHERE login = ?", (login.strip().lower(),))
        result = cursor.fetchone()
        if result is not None:
            return result
        else:
            raise UserNotFoundError()


class UserAuthSchema(BaseModel):
    login: str = Field(alias="login_placeholder", min_length=3, max_length=32)
    password: str = Field(alias="password_placeholder", min_length=3, max_length=64)




ntplib_client = ntplib.NTPClient()


@routerauth.post("/sign_in", description="user access")
def sign_in(userdata: Annotated[UserAuthSchema, Form()], response: Response):

    login = userdata.login.lower().strip()
    password = userdata.password

    def login_check(login: str, data: tuple) -> bool:
        login = login.strip().lower()
        if login == "login0":  # шо бы не регались под логином с примера
            return False
        elif len(data) > 1 and data[1] == login:
            return True
        return False

    def password_check(
        password: str, password_hash: str, try_count: int = 3
    ) -> dict | bool:
        ph = argon2.PasswordHasher()
        for _ in range(try_count):
            try:
                if ph.verify(password_hash, password):
                    return True
            except argon2.exceptions.VerificationError:  # для тестов функции
                return {
                    "message": "Неверный пароль или что-то сломалось. Повторите попытку.",
                    "type": "Error",
                }
            except argon2.exceptions.InvalidHashError:  # для тестов функции
                return {
                    "message": "Проблема с хэшем. Возможно запись в БД повреждена.",
                    "type": "Error",
                }
        return False

    data = get_users_by_login(login)
    dbtoken = data[5]  # индекс в кортеже data, где находится token_version

    if (
        login_check(login, data)
        and password_check(password, data[2], try_count=3) is True
    ):  # data[2] это индекс в кортеже где находится хэш пароля
        try:
            ntp_response = ntplib_client.request("pool.ntp.org", version=4)
        except (ntplib.NTPException, OSError):
            response.status_code = 503
            return {
                "message": "Ошибка подключения к pool.ntp.org серверу",
                "ok": False,
                }

        JWT_token = jwt.encode(
            {
                "sub": str(data[0]),  # data[0] это id пользователя в БД
                "role": "user",
                "logged": True,
                "exp": int(ntp_response.tx_time)
                + 86400,  # 86400 секунд это +1 день (жизнь токена 24 часа)
                "token_ver": dbtoken
            },
            settings.private_key,
            settings.algorithm,
        )  # settings.private_key это приватный ключ, JWT-токен обычно живет 15-60 минут, но для упрощения на данный момент сделаем 24 часа, позже вернем на 15 мин и сделаю refresh token.
        # settings.algorithm это алгоритм кодирования записанный в .env файле

        response.set_cookie(
            key="Authorization",
            value=JWT_token,
            max_age=86400,
            httponly=True,
            secure=False,  # позже поставить True, когда сайт будет на https://
        )

        return {"ok": True, "redirect_url":"/user"}
    else:
        response.status_code = 401
        return {"ok": False, "message":"Неправильный логин и/или пароль"}
        
        
        # return {
        #     "message": "Неправильный логин и/или пароль.\n1. Повторить попытку.\n2. Зарегистрироваться.",
        #     "bool": False,
        # }


@routerauth.post("/sign_up", description="user access")
def sign_up(userdata: Annotated[UserAuthSchema, Form()], response: Response):

    login = userdata.login.strip().lower()
    password = userdata.password

    data = ""

    def is_login_available(login) -> bool:
        nonlocal data
        try: 
            data = get_users_by_login(login)
        except UserNotFoundError:
            return True
        return False

    if is_login_available(login):
        try:
            ntp_response = ntplib_client.request("pool.ntp.org", version=4)
        except (ntplib.NTPException, OSError):
            response.status_code = 503
            return {
                "message": "Ошибка подключения к pool.ntp.org серверу",
                "ok": False,
            }

        utc_time = datetime.datetime.fromtimestamp(
            ntp_response.tx_time, tz=datetime.timezone.utc
        ).strftime("%Y-%m-%d")

        with sqlite3.connect(USERS_DB_NAME) as users:
            cursor = users.cursor()
            cursor.execute(
                "INSERT INTO Users (login, password_hash, role, reg_date, comment) VALUES (?, ?, ?, ?, ?)",
                (
                    login,
                    argon2.PasswordHasher().hash(password),
                    "user",
                    utc_time,  # дата регистрации в формате yyyy-mm-dd
                    None,
                ),
            )
            sub = cursor.lastrowid
            users.commit()

        JWT_token = jwt.encode(
            {
                "sub": str(sub),  # data[0] это id пользователя в БД
                "role": "user",
                "logged": True,
                "exp": int(ntp_response.tx_time)
                + 86400,  # 86400 секунд это +1 день (жизнь токена 24 часа)
                "token_ver": 1
            },
            settings.private_key,
            settings.algorithm,
        )  # settings.private_key это приватный ключ, JWT-токен обычно живет 15-60 минут, но для упрощения на данный момент сделаем 24 часа, позже вернем на 15 мин и сделаю refresh token.
        # settings.algorithm это алгоритм кодирования записанный в .env файле

        response.set_cookie(
            key="Authorization",
            value=JWT_token,
            max_age=86400,
            httponly=True,
            secure=False,  # позже поставить True, когда сайт будет на https://
        )

        return {"ok": True, "redirect_url":"/user"}
    else:
        response.status_code = 400
        return {"ok": False, "message":"Логин занят"}


class NotAuthenticated(Exception):
    pass


class JWT_check_from_cookie:
    def __init__(self, get_info: bool = False):
        self.get_info = get_info

    def __call__(self, auth_cookie: Annotated[str | None, Cookie(alias="Authorization")] = None):
        if auth_cookie is None:
                raise NotAuthenticated()
        else:
            try:
                payload = jwt.decode(
                    jwt=auth_cookie,
                    key=settings.public_key,
                    algorithms=[settings.algorithm],
                    verify=True,
                    )
    
                exp_date: int = payload["exp"]
                jwt_token_ver: int = payload["token_ver"]
                userid: str = payload["sub"]
    
                if not userid.isdigit():
                    raise NotAuthenticated()
                
                try:
                    with sqlite3.connect(USERS_DB_NAME) as users:
                        cursor = users.cursor()
                        cursor.execute(
                            "SELECT token_version FROM Users WHERE id = ?",
                            (int(userid),)
                            )
                        temp: tuple | None = cursor.fetchone()
                        users.commit()
    
                    if temp is None:
                        raise NotAuthenticated()
                    else:
                        db_token_ver: int = temp[0]
                                            
                except sqlite3.Error:
                    raise NotAuthenticated()
    
                try:
                    ntp_response = ntplib_client.request("pool.ntp.org", version=4)
                except (ntplib.NTPException, OSError):
                    raise NotAuthenticated()
    
                if exp_date > ntp_response.tx_time and jwt_token_ver == db_token_ver:
                    if self.get_info:
                        return {"ok": True, "db_token_ver": db_token_ver, "payload": payload}
                    else:
                        return True
                else:
                    raise NotAuthenticated()
    
            except jwt.PyJWTError:
                raise NotAuthenticated()

# def jwt_check_from_cookie(auth_cookie: Annotated[str | None, Cookie(alias="Authorization")] = None, get_info = False) -> bool:
#     if auth_cookie is None:
#         print("auth cookie none")
#         raise NotAuthenticated()
#     else:
#         try:
#             payload = jwt.decode(
#                 jwt=auth_cookie,
#                 key=settings.public_key,
#                 algorithms=[settings.algorithm],
#                 verify=True,
#                 )

#             exp_date: int = payload["exp"]
#             jwt_token_ver: int = payload["token_ver"]
#             userid: str = payload["sub"]

#             if not userid.isdigit():
#                 raise NotAuthenticated()
            
#             try:
#                 with sqlite3.connect(USERS_DB_NAME) as users:
#                     cursor = users.cursor()
#                     cursor.execute(
#                         "SELECT token_version FROM Users WHERE id = ?",
#                         (int(userid),)
#                         )
#                     temp: tuple | None = cursor.fetchone()
#                     users.commit()

#                 if temp is None:
#                     raise NotAuthenticated()
#                 else:
#                     db_token_ver: int = temp[0]
                                        
#             except sqlite3.Error:
#                 raise NotAuthenticated()

#             try:
#                 ntp_response = ntplib_client.request("pool.ntp.org", version=4)
#             except (ntplib.NTPException, OSError):
#                 print("ntp failed")
#                 raise NotAuthenticated()

#             if exp_date > ntp_response.tx_time and jwt_token_ver == db_token_ver:
#                 if get_info:
#                     return {"ok": True, "db_token_ver": db_token_ver, "payload": payload}
#                 else:
#                     return True
#             else:
#                 raise NotAuthenticated()

#         except jwt.PyJWTError:
#             raise NotAuthenticated()

class ChangePasswordError(Exception):
    pass

class UserChangePasswordSchema(BaseModel):
    old_password: str = Field(min_length=3, max_length=64, pattern=r"^[!-~№]+$")
    new_password: str = Field(min_length=3, max_length=64, pattern=r"^[!-~№]+$")

@routerauth.post("/change_password", description="user access")
def change_password(user_pswds: UserChangePasswordSchema, response: Response, full_info: Annotated[dict, Depends(JWT_check_from_cookie(get_info=True))]):
    old_pass = user_pswds.old_password
    new_pass = user_pswds.new_password
    payload: dict = full_info["payload"]
    sub = int(payload["sub"])

    try:
        with sqlite3.connect(USERS_DB_NAME) as users:
            cursor = users.cursor()
            cursor.execute("SELECT password_hash FROM Users WHERE id = ?", (sub,))
            temp: tuple | None = cursor.fetchone()
            users.commit()
                    
        if temp is None:
            raise ChangePasswordError()
        else:
            pswd_hash = temp[0]
    except sqlite3.Error:
        raise ChangePasswordError()

    ph = argon2.PasswordHasher()
    try:
        tmp_bool = ph.verify(pswd_hash, old_pass)
    except argon2.exceptions.VerificationError:  # для тестов функции
        raise ChangePasswordError()
    except argon2.exceptions.InvalidHashError:  # для тестов функции
        raise ChangePasswordError()
    except argon2.exceptions.VerifyMismatchError:
        raise ChangePasswordError()
    except argon2.exceptions.Argon2Error:
        raise ChangePasswordError()
        

    if old_pass == new_pass or (not tmp_bool):
        raise ChangePasswordError()
    else:
        new_pass_hash = ph.hash(new_pass)

        try:
            ntp_response = ntplib_client.request("pool.ntp.org", version=4)
        except (ntplib.NTPException, OSError):
            response.status_code = 503
            return {
                "message": "Ошибка подключения к pool.ntp.org серверу",
                "ok": False,
                }
        try:
            with sqlite3.connect(USERS_DB_NAME) as users:
                cursor = users.cursor()
                cursor.execute(
                    "UPDATE Users SET token_version = ?, password_hash = ?, comment = ? WHERE id = ?",
                    (
                        full_info["db_token_ver"] + 1,
                        new_pass_hash,
                        f"Password changed at {datetime.datetime.fromtimestamp(ntp_response.tx_time, tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')} by this user",
                        sub,
                    ),
                )
                users.commit()
        except sqlite3.Error:
            raise ChangePasswordError()
        return {"ok":True,"message": "Пароль успешно изменен"}

        
            


        
