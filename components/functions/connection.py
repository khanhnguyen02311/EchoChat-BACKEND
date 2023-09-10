from fastapi import WebSocket, HTTPException, status
from components.functions.security import handle_get_current_user


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, access_token: str):
        await websocket.accept()
        try:
            account = handle_get_current_user(access_token)
        except HTTPException as e:
            await websocket.send_text(f"Validation error: {e.detail}")
            await websocket.close()
            return False
        print(account.id)
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
