from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.v1.ws.manager import ws_manager
from app.core.metrics import ws_connections_current

router = APIRouter()


@router.websocket("/v1/ws/runs/{run_id}")
async def run_ws(websocket: WebSocket, run_id: int) -> None:
    await ws_manager.connect(run_id, websocket)
    ws_connections_current.inc()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(run_id, websocket)
        ws_connections_current.dec()
