from datetime import datetime
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from components.functions.security import handle_get_current_accountinfo
from components.data import PostgresSession
from components.functions.group import handle_check_joined_participant, handle_check_existed_group
from components.functions.message import handle_add_new_message, handle_get_messages_from_group, handle_get_pinned_messages, handle_pin_message, handle_unpin_message
from components.data.models import postgres_models as p_models, scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas

router = APIRouter(prefix="/group/{group_id}/messages")


@router.get("/all")
def get_message_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
                     group_id: uuid.UUID, before_time: datetime | None = None):

    if not handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")
    message_list = handle_get_messages_from_group(group_id, before_time)
    return message_list[:]


# @router.post("/new")
# async def add_new_message(message: s_schemas.MessagePOST,
#                           accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
#
#     try:
#         existed, group = handle_check_existed_group(message.group_id)
#         if not existed:
#             raise Exception("Group not existed")
#         message.accountinfo_name = accountinfo_token.name
#         message.group_name = group.name
#         error, new_group_message = handle_add_new_message(message)
#         if error is not None:
#             raise Exception(error)
#         return new_group_message
#
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=str(e))


# @router.delete("/delete")
# def delete_message(message: s_schemas.MessageMODIFY,
#                    accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
#     try:
#         message.accountinfo_name = accountinfo_token.name
#         error, new_group_message = handle_add_new_message(message)
#         if error is not None:
#             raise Exception(error)
#         return "Done"
#
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                             detail=str(e))


# TODO: working with pin transactions
@router.get("/pinned/all")
def get_pinned_messages(group_id: uuid.UUID, accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    if not handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")
    pinned_messages = handle_get_pinned_messages(group_id, accountinfo_token.id)
    return pinned_messages[:]


@router.post("/pinned/pin")
def pin_message(message: s_schemas.MessageMODIFY, group_id: uuid.UUID,
                accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    if not handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")
    error, new_message_pinned = handle_pin_message(message)
    if error is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(error))
    error, _ = handle_add_new_message(
        s_schemas.MessagePOST(group_id=new_message_pinned.group_id,
                              accountinfo_id=accountinfo_token.id,
                              group_name=new_message_pinned.group_name,
                              accountinfo_name=accountinfo_token.name,
                              type=s_models.CONSTANT.Message_type[2],
                              content=f"User {accountinfo_token.name} pinned a message."))
    return new_message_pinned


@router.delete("/pinned/unpin")
def unpin_message(message: s_schemas.MessageMODIFY, group_id: uuid.UUID,
                  accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    if not handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")
    error, unpinned_message = handle_unpin_message(message)
    if error is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(error))
    error, _ = handle_add_new_message(
        s_schemas.MessagePOST(group_id=unpinned_message.group_id,
                              accountinfo_id=accountinfo_token.id,
                              group_name=unpinned_message.group_name,
                              accountinfo_name=accountinfo_token.name,
                              type=s_models.CONSTANT.Message_type[2],
                              content=f"User {accountinfo_token.name} unpinned a message."))
    return "Done"
