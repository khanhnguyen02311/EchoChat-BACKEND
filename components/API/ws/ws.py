from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, WebSocketException, status

from components.functions.connection import ConnectionManager
from components.functions.security import handle_get_current_accountinfo

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/connect")
async def chat_endpoint(websocket: WebSocket, token: str):
    try:
        accountinfo = handle_get_current_accountinfo(token)
    except HTTPException as e:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
    # if self.active_connections.get(account.id) is not None: # implement later

    await manager.connect(websocket)
    # await manager.send_personal_message("Account connect successfully.", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.read_message(accountinfo, data, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
