from fastapi import WebSocket
from components.functions.chat import handle_add_message


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def read_message(self, account_id, message: dict, websocket: WebSocket):
        try:
            type = message['type']  # for later if needed
            action = message['action']
            group_id = message['group']
            content = message['content']
            if action == "new":
                created_message = handle_add_message(account_id, group_id, content)
                if created_message is None:
                    raise Exception("Invalid group")
                await self.send_personal_message(f"SUCCESSFUL: {content}", websocket)

        except Exception as e:
            await self.send_personal_message(f"UNSUCCESSFUL: {str(e)}", websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
