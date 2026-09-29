import asyncio
import json

from websockets.asyncio.client import connect

# from websockets.asyncio.server import serve
from websockets.exceptions import WebSocketException

from agent_settings import settings



# auth для рукопожатия и передачи токена, heartbeat для поддержания связи, command для команды от мастера, result для ответа от агента, error при сбое
package_type = {"auth": "auth", "heartbeat": "heartbeat", "command": "command", "result": "result", "error": "error"}  # для alias можно менять ключи

class wsError(Exception):
    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(*args)
        self.message = message
        print(self.message)


# async def handler(websocket):
#     async with connect(uri=fastapi_server, ping_interval=60) as websocket:
#         try:
#             await websocket.send("hello from test server")
#         except WebSocketException:
#             raise wsError("упал вебсокет")

# async def main():
#     server = await serve(handler, "127.0.0.1", 8000)
#     await server.serve_forever()

async def ping():
    pass

async def task_reader(websocket):
    received_bytes = await websocket.recv()
    received = json.loads(received_bytes)
    print(received)
    return received

async def heartbeat_task(websocket):
    await asyncio.sleep(30)
    data = {"type":package_type.get("heartbeat", None), "status": "ok", "data": heartbeat_data}
    data_in_bytes = json.dumps(data, ensure_ascii=False).encode()
    await websocket.send(data_in_bytes)
    heartbeat_result_in_bytes = await websocket.re

async def run_agent_session(server_uri: str | None):
    async with connect(uri=server_uri) as websocket:
        print("Открыли коннект с websocket")
        try:
            # data или error могут не заполняться или вообще не быть словаре в зависимости от значения у ключа "status" и "type"
            default_data = {"type":package_type.get("auth", "error"), "status": "ok", "data": "тут данные при статус ok", "error": "тут сообщение об ошибке при статус error"}
            
            heartbeat_data = {"heart": True}  # в ответ {"beat": True}
            actions = {"ping": ping}  # белый список функций которые могут исполняться на сервере
            handshake = {"hello":True}  # первое рукопожатие при старте коннекта
            dct_in_bytes = json.dumps(handshake, ensure_ascii=False).encode()

            task = asyncio.create_task(task_reader(websocket))
            heartbeat = asyncio.create_task(heartbeat_task(websocket))

            done, pending = await asyncio.wait((task, heartbeat), return_when=asyncio.FIRST_COMPLETED)

            for finished_task in done:
                err = finished_task.exception()
                if err:
                    print("Ошибка в выполненной задаче", err)

            for unfinished_task in pending:
                unfinished_task.cancel()
                try:
                    await unfinished_task
                except asyncio.CancelledError():
                    pass






            await websocket.send(dct_in_bytes)
            received = task_reader()
            
            if type(received) is dict:
                try:
                    if received["action"] in actions:
                        if received["action"] == "ping":
                            dct = {"step":3, "status":actions["ping"]}
                            dct_in_bytes = json.dumps(dct, ensure_ascii=False).encode()
                            await websocket.send(dct_in_bytes)
                        else:
                            raise wsError("действие не пинг, а других пока нет")
                    else:
                        raise wsError("переданные действия не найдены в разрешенных")
                except KeyError:
                    raise wsError("нет ключа в словаре")
            else:
                raise wsError("падение из-за неправильного типа данных полученных от сервера fastapi")
            
        except WebSocketException:
            raise wsError("упал вебсокет")


async def main_supervisor(server_uri: str | None = None):
    retry_delay = 1
    max_delay = 35

    if server_uri:
        while True:
            try:
                
                    run_agent_session(server_uri=server_uri)
                    retry_delay = 1
                
            except (ConnectionError, OSError) as expected_err:
                asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
                print("Словили ошибку о штатном закрытии вебсокета", expected_err)
            except Exception as unexpected_err:  # noqa: BLE001
                asyncio.sleep(retry_delay)
                print("Словили неожиданную ошибку", unexpected_err)
    else:
        raise wsError("адрес сервера не передан")


if __name__ == "__main__":
    fastapi_server = settings.fastapi_server + "/ws/agent"  # адрес сервера типа ws:// или wss:// и + адрес обработчика
    asyncio.run(main_supervisor(server_uri = fastapi_server))