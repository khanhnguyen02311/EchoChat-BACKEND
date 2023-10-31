from fastapi import APIRouter, WebSocketDisconnect, WebSocketException, status

from components.utilities.connection_manager import ConnectionManager
from components.functions.security import handle_get_current_accountinfo
from components.utilities.websocket import CustomWebSocket

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/connect")
async def chat_endpoint(websocket: CustomWebSocket, token: str):
    try:
        accountinfo = handle_get_current_accountinfo(token)
    except Exception as e:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))
    # if self.active_connections.get(account.id) is not None: # implement later

    await manager.connect(websocket, accountinfo)
    try:
        while True:
            new_message = await websocket.receive_json()
            await manager.read_conn_message(websocket, new_message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
