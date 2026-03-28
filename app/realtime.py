from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import DefaultDict

from fastapi import WebSocket


class WebSocketHub:
    def __init__(self) -> None:
        self._connections: DefaultDict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, username: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[username].add(websocket)

    async def disconnect(self, username: str, websocket: WebSocket) -> None:
        async with self._lock:
            if username in self._connections and websocket in self._connections[username]:
                self._connections[username].remove(websocket)
                if not self._connections[username]:
                    del self._connections[username]

    async def broadcast(self, payload: dict) -> None:
        async with self._lock:
            sockets = [ws for user_set in self._connections.values() for ws in user_set]

        disconnected: list[tuple[str, WebSocket]] = []
        for websocket in sockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.extend(
                    (username, websocket)
                    for username, user_set in self._connections.items()
                    if websocket in user_set
                )

        for username, websocket in disconnected:
            await self.disconnect(username, websocket)
