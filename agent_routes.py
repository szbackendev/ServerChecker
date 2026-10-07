from typing import Annotated

import jwt
from fastapi import APIRouter, Cookie, Depends

from settings import settings

router_agent = APIRouter(prefix="/api/agent", tags=["Agent"])

class AgentError(Exception):  # общий класс для всех ошибок в agent_routes.py
    pass


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

@router_agent.get(path="/stream")
async def agent_connection(user_id: Annotated[str, Depends(get_user_id)]):

    if user_id in (0, "0"):
        raise AgentError

    # подумать как реализовать проверку ip без пользователя и его jwt токена
    # если пользователь спит а Агент спрашивает или выполнил задачу, то jwt токен не получить и не сверить принадлежит ли этот сервер нужному пользователю

    # доделать SSE соединение на этап постоянно стрима между Агентом и Мастером