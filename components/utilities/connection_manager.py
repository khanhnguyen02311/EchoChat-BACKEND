import asyncio
import uuid
from enum import Enum
from typing import Any
from pydantic import BaseModel, constr, conint, Field
from components.utilities.websocket import CustomWebSocket
from components.data.models import scylla_models as s_models, postgres_models as p_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas
from components.functions.message import handle_add_new_message
from components.functions.group import handle_get_all_participants, handle_check_existed_group


class ConnMsgType(str, Enum):
    message = "message"
    notification = "notification"
    response = "response"
    help = "help"


# class ConnMsgAction(str, Enum):
#     new = "new"
#     delete = "delete"


class ConnMsgStatus(str, Enum):
    success = "success"
    error = "error"
    other = "other"


class ConnMsg(BaseModel):
    type: ConnMsgType
    status: ConnMsgStatus | None = None
    data: Any
    # action: ConnMsgAction | None = None


class Conn:
    def __init__(self, websocket: CustomWebSocket, accountinfo: p_models.Accountinfo):
        self.websocket = websocket
        self.accountinfo = accountinfo


class ConnectionManager:
    conns_by_id: dict[int, Conn]
    conns_by_ws: dict[CustomWebSocket, Conn]

    def __init__(self):
        self.conns_by_id = {}
        self.conns_by_ws = {}

    async def connect(self, websocket: CustomWebSocket, accountinfo: p_models.Accountinfo):
        await websocket.accept()
        new_active_connection = Conn(websocket, accountinfo)
        self.conns_by_id[accountinfo.id] = new_active_connection
        self.conns_by_ws[websocket] = new_active_connection

    def disconnect(self, websocket: CustomWebSocket):
        active_connection = self.conns_by_ws.get(websocket)
        self.conns_by_ws.pop(websocket)
        self.conns_by_id.pop(active_connection.accountinfo.id)

    async def read_conn_message(self, websocket: CustomWebSocket, message: dict):
        try:
            conn_message = ConnMsg.model_validate(message)
            if conn_message.type == ConnMsgType.help:
                await self.send_personal_conn_message(websocket, ConnMsg(type=ConnMsgType.response,
                                                                         status=ConnMsgStatus.success,
                                                                         data=ConnMsg.model_json_schema()))

            elif conn_message.type == ConnMsgType.message:
                message_data = s_schemas.MessagePOST.model_validate(conn_message.data)
                existed, group = handle_check_existed_group(message_data.group_id, allow_private_groups=True)
                if not existed:
                    raise Exception("Group not found")
                ws_accountinfo = self.conns_by_ws.get(websocket).accountinfo
                message_data.accountinfo_id = ws_accountinfo.id
                message_data.accountinfo_name = ws_accountinfo.name
                message_data.group_name = group.name
                error, new_group_message = handle_add_new_message(message_data)
                if error is not None:
                    raise Exception(error)

                new_group_message = s_schemas.MessageGET.model_validate(new_group_message).model_dump(mode="json")
                await self.send_personal_conn_message(websocket, ConnMsg(type=ConnMsgType.response,
                                                                         status=ConnMsgStatus.success,
                                                                         data=None))
                await self.send_message_notifications(new_group_message)

        except Exception as e:
            await self.send_personal_conn_message(websocket, ConnMsg(type=ConnMsgType.response,
                                                                     status=ConnMsgStatus.error,
                                                                     data=str(e)))

    async def send_personal_conn_message(self, websocket: CustomWebSocket, conn_message: ConnMsg):
        await websocket.send_json(conn_message.model_dump())

    async def send_message_notifications(self, new_group_message: dict):
        existed, participant_list = handle_get_all_participants(uuid.UUID(new_group_message['group_id']),
                                                                with_accountinfo=False)
        available_conns = []
        for row in participant_list:
            connection = self.conns_by_id.get(row.accountinfo_id)
            if connection is not None:
                available_conns.append(self.send_personal_conn_message(connection.websocket,
                                                                       ConnMsg(type=ConnMsgType.notification,
                                                                               data=new_group_message)))
        # print(available_conns)
        await asyncio.gather(*available_conns)
        # if error is not None:
        #     await self.send_personal_conn_message(websocket, ConnMsg(type=ConnMsgType.response,
        #                                                              status=ConnMsgStatus.error,
        #                                                              data=str(e)))

    async def broadcast(self, message: str):
        pass


global_connection_manager = ConnectionManager()
