from datetime import datetime
import uuid
from enum import Enum

from fastapi import WebSocket
from pydantic import BaseModel, constr, conint
from components.storages.models import scylla_models as s_models, postgres_models as p_models
from components.storages.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas
from components.functions.group import handle_check_joined_participant


# class MessageAction(str, Enum):
#     message_new = "msg_new"
#     message_del = "msg_del"
#     message_pin = "msg_pin"
#
#
# class ConnectionMessage(BaseModel):
#     message_from: str


def handle_add_group_message(group_id: uuid.UUID,
                             accountinfo_id: int,
                             content: str,
                             accountinfo_name: str | None,
                             group_name: str | None,
                             message_type: str = s_models.CONSTANT.Message_type[0]):
    """Add group message for provided account and group. Return  \n
    Return: (error, new_message)"""

    existed, participant = handle_check_joined_participant(group_id, accountinfo_id)
    if existed:
        time = datetime.utcnow()
        new_message = s_schemas.MessagePOST(content=content,
                                            group_id=group_id,
                                            accountinfo_id=accountinfo_id,
                                            type=message_type,
                                            group_name=group_name,
                                            accountinfo_name=accountinfo_name,
                                            time_created=time)
        s_models.MessageByAccount.create(**new_message.model_dump())
        new_message_by_group = s_models.MessageByGroup.create(**new_message.model_dump())
        return None, new_message_by_group
    return "Account not in group", None


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def read_message(self, accountinfo_id: p_models.Accountinfo, message: dict, websocket: WebSocket):
        try:
            await self.send_personal_message(f"SUCCESSFUL", websocket)

        except Exception as e:
            await self.send_personal_message(f"UNSUCCESSFUL: {str(e)}", websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
