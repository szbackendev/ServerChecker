# from re import search as re_search
from re import match as re_match
from auth import USERS_DB_NAME
from settings import settings
import sqlite3
from fastapi import APIRouter, Cookie, Depends
from typing import Annotated
import jwt

routerips = APIRouter(prefix="/ips", tags=["IPs"])


DEF_SERVER_IP = "1.1.1.1"


def funcs_choice():
    pass  # тоже пока не понятно как это будет в интерфейсе сайта выглядить и нужна ли вообще эта функция


def get_user_id(
    auth_cookie: Annotated[str | None, Cookie(alias="Authorization")] = None,
):
    # логин по идее должен браться из JWT-токена, который есть в куки

    if auth_cookie is None:
        return 0

    user_id = jwt.decode(
        jwt=auth_cookie,
        key=settings.public_key,
        algorithms=settings.algorithm,
        verify=True,
    )["sub"]

    return user_id


@routerips.get("/get_ips", description="user access")
def prev_IPs(
    user_id: Annotated[str, Depends(get_user_id)],
):  # проверка есть ли таблица known_IPs, если нет то вернуть строку: 'список пред. адресов пуст', если есть то вернуть все 5 ip.

    if user_id == "0":
        return {"message": "Ошибка во взятии user_id из payload JWT-токена"}

    with sqlite3.connect(USERS_DB_NAME) as users:
        cursor = users.cursor()
        cursor.execute("""SELECT EXISTS (
                       SELECT 1
                       FROM sqlite_master
                       WHERE type = 'table' AND name = 'known_IPs'
                       )""")
        if cursor.fetchone()[0] == 0:
            return {"message": "Список предыдущих IP-адресов пуст."}
        else:
            cursor.execute(
                """SELECT ip FROM known_IPs WHERE user_id = ? ORDER BY id DESC""",
                (user_id,),
            )
            ips = cursor.fetchall()

            if len(ips) == 0:
                return {"message": "Список предыдущих IP-адресов пуст."}
            else:
                list_of_ips = list(ip[0] for ip in ips)
                return {"IPs": list_of_ips}


@routerips.post("/new_ip", description="user access")
def new_IP(
    user_id: Annotated[str, Depends(get_user_id)], user_ip: str
) -> dict:  # должна возвращать новый IP-адрес и записывать его в known_IPs.txt

    if user_id == "0":
        return {"message": "Ошибка во взятии user_id из payload JWT-токена"}

    if not re_match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", user_ip):
        return {"message": "Введенная строка не является IP-адресом. Формат: X.X.X.X"}

    with sqlite3.connect(USERS_DB_NAME) as users:
        cursor = users.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS known_IPs (
                       id INTEGER PRIMARY KEY,
                       user_id INTEGER NOT NULL,
                       ip TEXT NOT NULL,
                       UNIQUE(user_id, ip)
                       )""")

        cursor.execute(
            "INSERT OR IGNORE INTO known_IPs (user_id, ip) VALUES (?,?)",
            (user_id, user_ip),
        )

        cursor.execute("SELECT COUNT(*) FROM known_IPs WHERE user_id = ?", (user_id,))

        if cursor.fetchone()[0] > 5:
            cursor.execute(
                "DELETE FROM known_IPs WHERE user_id = ? AND id = (SELECT MIN(id) FROM known_IPs WHERE user_id = ?)",
                (user_id, user_id),
            )

        users.commit()
    return {
        "message": f"Успешно добавлен IP-адрес: {user_ip}",
        "new_ip": user_ip,
    }


def ip_choice():
    pass  # на сайте пользователь сам будет тыкать что-то на интерфейсе что вызовет либо new_ip, либо prev_ips, пока не уверен нужна функция или нет
