import json
from pprint import pprint
from datetime import datetime
import uuid
from enum import Enum
from typing import Any
from pydantic import BaseModel, constr, conint, Field
from components.utilities.websocket import CustomWebSocket
from components.data.models import scylla_models as s_models, postgres_models as p_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas
from components.functions.message import handle_add_new_message


class ConnMsgType(str, Enum):
    message = "message"
    notification = "notification"
    response = "response"
    help = "help"


class ConnMsgAction(str, Enum):
    new = "new"
    delete = "delete"


class ConnMsgStatus(str, Enum):
    success = "success"
    error = "error"
    other = "other"


class ConnMsg(BaseModel):
    type: ConnMsgType
    status: ConnMsgStatus | None = None
    action: ConnMsgAction | None = None
    data: Any


class Conn:
    def __init__(self, websocket: CustomWebSocket, accountinfo: p_models.Accountinfo):
        self.websocket = websocket
        self.accountinfo = accountinfo


class ConnectionManager:
    def __init__(self):
        self.conns_by_id = {}
        self.conns_by_ws = {}

    async def connect(self, websocket: CustomWebSocket, accountinfo: p_models.Accountinfo):
        await websocket.accept()
        new_active_connection = Conn(websocket, accountinfo)
        self.conns_by_id[accountinfo.id] = new_active_connection
        self.conns_by_ws[websocket] = new_active_connection

        # print(f"New connection: {websocket.client.host}:{websocket.client.port}")
        # pprint(self.conns_by_id)
        # pprint(self.conns_by_ws)

    def disconnect(self, websocket: CustomWebSocket):
        active_connection = self.conns_by_ws.get(websocket)
        self.conns_by_ws.pop(websocket)
        self.conns_by_id.pop(active_connection.accountinfo.id)

    async def read_conn_message(self, websocket: CustomWebSocket, message: dict):
        try:
            validated_message = ConnMsg.model_validate(message)
            if validated_message.type == ConnMsgType.help:
                await self.send_personal_conn_message(websocket, ConnMsg(type=ConnMsgType.response,
                                                                         status=ConnMsgStatus.success,
                                                                         data=ConnMsg.model_json_schema()))

            elif validated_message.type == ConnMsgType.message:
                if validated_message.action == ConnMsgAction.new:
                    print(validated_message.data)
                    message_data = s_schemas.MessagePOST.model_validate(validated_message.data)
                    message_data.accountinfo_id = self.conns_by_ws.get(websocket).accountinfo.id
                    # group_message.accountinfo_name = self.conns_by_ws.get(websocket).accountinfo.name
                    error, group_message = handle_add_new_message(message_data)
                    if error is not None:
                        raise Exception(error)

                    group_message = s_schemas.MessageGET.model_validate(group_message).model_dump(mode="json")
                    await self.send_personal_conn_message(websocket, ConnMsg(type=ConnMsgType.response,
                                                                             status=ConnMsgStatus.success,
                                                                             data=group_message))

                elif validated_message.action == ConnMsgAction.delete:
                    pass

        except Exception as e:
            await self.send_personal_conn_message(websocket, ConnMsg(type=ConnMsgType.response,
                                                                     status=ConnMsgStatus.error,
                                                                     data=str(e)))

    async def send_personal_conn_message(self, websocket: CustomWebSocket, message: ConnMsg):
        await websocket.send_json(message.model_dump())

    async def broadcast(self, message: str):
        pass
