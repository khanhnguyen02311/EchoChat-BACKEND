from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, WebSocketException, status
from components.functions.connection import ConnectionManager
from components.functions.security import handle_get_current_user

router = APIRouter(prefix="/message")

# manager = ConnectionManager()
#
# @router.websocket("/connect")
# async def chat_endpoint(websocket: WebSocket, token: str):
#     try:
#         account = handle_get_current_user(token)
#     except HTTPException as e:
#         print("Account not validated:", e.detail)
#         raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=e.detail)
#     # if self.active_connections.get(account.id) is not None: # implement later
#     print(account.id)
#
#     await manager.connect(websocket)
#     await manager.send_personal_message(f"{account.username} connect successfully.", websocket)
#     try:
#         while True:
#             data = await websocket.receive_json()
#             await manager.read_message(account.id, data, websocket)
#
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
