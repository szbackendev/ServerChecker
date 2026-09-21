import asyncio
import json

from websockets.asyncio.client import connect

# from websockets.asyncio.server import serve
from websockets.exceptions import WebSocketException

from settings import settings

fastapi_server = settings.fastapi_server + "/ws/agent"

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

async def test():
    async with connect(uri=fastapi_server, ping_interval=60) as websocket:
        try:
            actions = {"ping": "pong"}
            dct = {"hello":True}
            dct_in_bytes = json.dumps(dct, ensure_ascii=False).encode()

            await websocket.send(dct_in_bytes)
            received_bytes = await websocket.recv()
            received = json.loads(received_bytes)
            print(received)
            if type(received) is dict:
                try:
                    if received["action"] in actions:
                        if received["action"] == "ping":
                            dct = {"status":actions["ping"]}
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

if __name__ == "__main__":
    asyncio.run(test())