from fastapi import HTTPException

from . import EchoChat_pb2, EchoChat_pb2_grpc
from components.functions.security import handle_get_current_accountinfo
from components.functions.message import handle_add_new_message
from components.data.schemas import scylla_schemas as s_schemas


class BEServicerGRPC(EchoChat_pb2_grpc.EchoChatBEServicer):
    def ValidateToken(self, request, context):
        try:
            accountinfo = handle_get_current_accountinfo(request.token)
            return EchoChat_pb2.AccountinfoValue(id=accountinfo.id,
                                                 name=accountinfo.name,
                                                 identifier=accountinfo.identifier)
        except HTTPException as e:
            return EchoChat_pb2.AccountinfoValue(id=-1, name=e.detail, identifier=0)

    def NewMessage(self, request, context):
        input_message = s_schemas.MessagePOST(group_id=request.group_id,
                                              accountinfo_id=request.accountinfo_id,
                                              accountinfo_name=request.accountinfo_name,
                                              content=request.content,
                                              type=request.type)
        err, new_message = handle_add_new_message(input_message)
        if err is not None:
            return EchoChat_pb2.NewMessageResult(result=False, error=err)
        return EchoChat_pb2.NewMessageResult(result=True)
