import json
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from components.functions.security import handle_get_current_accountinfo
from components.data import PostgresSession
from components.functions.group import handle_check_joined_participant, handle_check_existed_group
from components.functions.message import handle_add_new_message
from components.data.models import postgres_models as p_models, scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas
from components.utilities.connection_manager import global_connection_manager

router = APIRouter(prefix="/group/{group_id}/messages")


@router.get("/all")
def get_message_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
                     group_id: uuid.UUID):
    if handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        message_list = s_models.MessageByGroup.objects.filter(group_id=group_id).all()
        return message_list[:]

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")


@router.post("/new")
async def add_new_message(message: s_schemas.MessagePOST, group_id: uuid.UUID,
                          accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        message.accountinfo_name = accountinfo_token.name
        error, new_group_message = handle_add_new_message(message)
        if error is not None:
            raise Exception(error)
        await global_connection_manager.send_message_notifications(
            s_schemas.MessageGET.model_validate(new_group_message).model_dump(mode="json"))
        return "Done"

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.delete("/delete")
def delete_message(message: s_schemas.MessagePOST, group_id: uuid.UUID,
                   accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        message.accountinfo_name = accountinfo_token.name
        error, new_group_message = handle_add_new_message(message)
        if error is not None:
            raise Exception(error)
        return "Done"

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.get("/pinned/all")
def get_pinned_messages(group_id: uuid.UUID, accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    # if handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
    #     s_models.MessagePinned.objects.all()
    pass


@router.post("/pinned/pin")
def pin_message(message: s_schemas.MessageGET, group_id: uuid.UUID,
                accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    pass


@router.delete("/pinned/unpin")
def unpin_message(message: s_schemas.MessageGET, group_id: uuid.UUID,
                  accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    pass