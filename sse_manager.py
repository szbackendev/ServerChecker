
import asyncio


class AgentStreamManager:
    def __init__(self) -> None:
        self._streams: dict[str, asyncio.Queue] = {}