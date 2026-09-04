from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.v1.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/live")
async def live_feed(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Client doesn't need to send anything; keep the socket alive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
