from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class RunWsManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, run_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[run_id].add(websocket)

    async def disconnect(self, run_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            if run_id in self._connections and websocket in self._connections[run_id]:
                self._connections[run_id].remove(websocket)
            if run_id in self._connections and not self._connections[run_id]:
                del self._connections[run_id]

    async def broadcast(self, run_id: int, payload: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._connections.get(run_id, set()))
        for ws in targets:
            await ws.send_json(payload)


ws_manager = RunWsManager()
