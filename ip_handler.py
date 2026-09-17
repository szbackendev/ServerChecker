# from re import search as re_search
import sqlite3
from re import match as re_match
from typing import Annotated

import jwt
from fastapi import APIRouter, Cookie, Depends, Response

from settings import settings

routerips = APIRouter(prefix="/ips", tags=["IPs"])


DEF_SERVER_IP = "1.1.1.1"
USERS_DB_NAME = settings.USERS_DB_NAME

class ip_handler_error(Exception):  # общий класс для всех ошибок в ip_handler.py
    pass

def funcs_choice():
    pass  # тоже пока не понятно как это будет в интерфейсе сайта выглядить и нужна ли вообще эта функция


def get_user_id(
    auth_cookie: Annotated[str | None, Cookie(alias="Authorization")] = None,
):
    # логин по идее должен браться из JWT-токена, который есть в куки

    if auth_cookie is None:
        return 0

    try:
        jwt_payload = jwt.decode(
            jwt=auth_cookie,
            key=settings.public_key,
            algorithms=[settings.algorithm],
            verify=True,
            )
    except jwt.PyJWTError:
        return 0

    try:
        user_id = jwt_payload["sub"]
    except KeyError:
        return 0

    return user_id


@routerips.get("/get_ips", description="user access")
def prev_IPs(
    user_id: Annotated[str, Depends(get_user_id)],
response: Response):  # проверка есть ли таблица known_IPs, если нет то вернуть строку: 'список пред. адресов пуст', если есть то вернуть все 5 ip.

    if user_id in (0, "0"):
        raise ip_handler_error()

    try:
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
                    list_of_ips = [ip[0] for ip in ips]
                    return {"IPs": list_of_ips}
    except sqlite3.Error:
        raise ip_handler_error()
        


@routerips.post("/new_ip", description="user access")
def new_IP(
    user_id: Annotated[str, Depends(get_user_id)], user_ip: str
) -> dict:  # должна возвращать новый IP-адрес и записывать его в known_IPs.txt

    if user_id == "0":
        return {"message": "Ошибка во взятии user_id из payload JWT-токена"}

    if not re_match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", user_ip):
        return {"message": "Введенная строка не является IP-адресом. Формат: X.X.X.X"}

    try:
        with sqlite3.connect(USERS_DB_NAME) as users:
            cursor = users.cursor()
    
            cursor.execute(
                "INSERT OR IGNORE INTO known_IPs (user_id, ip, is_active) VALUES (?,?,?)",
                (user_id, user_ip, 0),
            )
    
            cursor.execute("SELECT COUNT(*) FROM known_IPs WHERE user_id = ?", (user_id,))
    
            if cursor.fetchone()[0] > 5:
                cursor.execute(
                    "DELETE FROM known_IPs WHERE user_id = ? AND id = (SELECT MIN(id) FROM known_IPs WHERE user_id = ?)",
                    (user_id, user_id),
                )
    
            users.commit()
    except sqlite3.Error as e:
        raise ip_handler_error()
        
    return {
        "message": f"Успешно добавлен IP-адрес: {user_ip}",
        "new_ip": user_ip,
    }


def ip_choice():
    pass  # на сайте пользователь сам будет тыкать что-то на интерфейсе что вызовет либо new_ip, либо prev_ips, пока не уверен нужна функция или нет
