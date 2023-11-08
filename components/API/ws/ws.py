from fastapi import APIRouter, WebSocketDisconnect, WebSocketException, status
from configurations.conf import Env
from components.utilities.connection_manager import global_connection_manager
from components.functions.security import handle_get_current_accountinfo
from components.utilities.websocket import CustomWebSocket

router = APIRouter()


@router.websocket("/connect")
async def chat_endpoint(websocket: CustomWebSocket, token: str):
    try:
        accountinfo = handle_get_current_accountinfo(token)
    except Exception as e:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))

    await global_connection_manager.connect(websocket, accountinfo)
    if Env.APP_DEBUG:
        print("CONNS_BY_ID: \n\t", global_connection_manager.conns_by_id)
        print("CONNS_BY_WS: \n\t", global_connection_manager.conns_by_ws)
    try:
        while True:
            new_message = await websocket.receive_json()
            await global_connection_manager.read_conn_message(websocket, new_message)

    except WebSocketDisconnect:
        global_connection_manager.disconnect(websocket)
