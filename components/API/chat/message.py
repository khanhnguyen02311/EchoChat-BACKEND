from components.functions.connection import ConnectionManager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/message")

manager = ConnectionManager()


@router.websocket("/connect")
async def chat_endpoint(websocket: WebSocket, token: str):
    succeed = await manager.connect(websocket, token)
    if not succeed:
        return
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client left the chat")
