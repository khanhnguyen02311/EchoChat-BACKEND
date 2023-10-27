import json
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from components.functions.security import handle_get_current_accountinfo
from components.functions.group import handle_create_new_group, handle_get_personal_groups, handle_add_new_participant, \
    handle_check_joined_participant, handle_check_existed_group
from components.storages import PostgresSession
from components.storages.models import postgres_models as p_models, scylla_models as s_models
from components.storages.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas

router = APIRouter()


@router.get("/group/recent")
def get_group_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    return handle_get_personal_groups(accountinfo_token.id)


@router.post("/group/create")
def create_new_group(group_info: s_schemas.GroupPOST,
                     accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        list_participant_accountinfo = [accountinfo_token]  # add accounts when create group if needed later
        error_list, created_group = handle_create_new_group(group_info, list_participant_accountinfo)
        if error_list is not None:
            raise Exception(str(error_list))
        return created_group

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e)


@router.post("/group/join")
def join_group(group_id: uuid.UUID,
               accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        existed, group = handle_check_existed_group(group_id)
        if existed:
            ## checking group visibility or group invitation notification, leave for later ##
            
            error, new_participant = handle_add_new_participant(group_id, accountinfo_token.id,
                                                                group_name=group.name,
                                                                accountinfo_name=accountinfo_token.name,
                                                                with_notification=True)
            if error is not None:
                raise Exception(error)
            return new_participant

        raise Exception("Group not found")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e)


# @router.post("/group/leave")
# def leave_group(group_id: uuid.UUID,
#                 accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
#     try:
#         if handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
#             pass
#
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/group/{group_id}/messages")
def get_message_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
                     group_id: uuid.UUID):
    if handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        message_list = s_models.MessageByGroup.objects.filter(group_id=group_id).all()
        return message_list[:]

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")


@router.get("/group/{group_id}/participants")
def get_group_participant_list(
        accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
        group_id: uuid.UUID):
    if handle_check_joined_participant(group_id, accountinfo_token.id)[0]:

        result_list = []
        participant_list = s_models.ParticipantByGroup.objects.filter(group_id=group_id).all()
        with PostgresSession.begin() as session:
            for row in participant_list:
                user_query = select(p_models.Accountinfo).where(p_models.Accountinfo.id == row.accountinfo_id)
                accountinfo = session.scalar(user_query)
                result_list.append(
                    {**s_schemas.ParticipantPOST.model_validate(row).model_dump(),
                     **p_schemas.AccountinfoSchemaGET.model_validate(accountinfo).model_dump()})
        return result_list

    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail="You are not a participant of the group")
