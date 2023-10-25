import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from components.functions.security import handle_get_current_accountinfo
from components.functions.chat import handle_create_new_group, handle_get_personal_groups, handle_add_new_participant, \
    handle_check_existed_participant
from components.storages.models import postgres_models as p_models, scylla_models as s_models
from components.storages.schemas import scylla_schemas as s_schemas

router = APIRouter()


@router.get("/group/recent")
def get_group_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    return handle_get_personal_groups(accountinfo_token.id)


@router.post("/group/create")
def create_new_group(group_info: s_schemas.GroupPOST,
                     accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        list_participant_accountinfo = [accountinfo_token]  # add accounts when create group if needed later
        error, created_group = handle_create_new_group(group_info, list_participant_accountinfo)
        if error is not None:
            raise Exception(error)
        return created_group

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/group/join")
def join_group(group_id: uuid.UUID,
               accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):

    try:
        existed_group = s_models.Group.objects.filter(id=group_id).first()
        if existed_group is not None:
            ## checking group visibility or group invitation notification, leave for later ##

            error, new_participant = handle_add_new_participant(group_id=existed_group.id,
                                                                accountinfo_id=accountinfo_token.id,
                                                                group_name=existed_group.name,
                                                                accountinfo_name=accountinfo_token.name,
                                                                with_notification=True)
            if error is not None:
                raise Exception(error)
            return new_participant

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/group/{group_id}/messages")
def get_message_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
                     group_id: uuid.UUID):
    if handle_check_existed_participant(group_id, accountinfo_token.id):
        pass
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")
#
#
# @router.get("/list/{groupid}/participants")
# def get_group_participant_list(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_user_oauth2)],
#                                group_id: str):
#     valid_participant = handle_get_participant_by_account_and_group(token_account.id, group_id)
#     if valid_participant is not None:
#         result_list = []
#         participants = handle_get_participants_by_group(group_id)
#         for i in participants:
#             result_list.append(i.id_account)
#         return result_list
#
#     return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                          detail="You are not a participant of the group")
#
#
