import json
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from components.functions.security import handle_get_current_accountinfo
from components.functions.group import handle_add_new_group, handle_get_personal_groups, handle_add_new_participant, \
    handle_check_joined_participant, handle_check_existed_group, handle_get_all_participants, handle_remove_participant
from components.data import PostgresSession
from components.data.models import postgres_models as p_models, scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas
from components.utilities.connection_manager import global_connection_manager

router = APIRouter(prefix="/group")


@router.get("/recent")
def get_group_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    return handle_get_personal_groups(accountinfo_token.id)


@router.post("/create")
async def create_new_group(group_info: s_schemas.GroupPOST,
                           accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        error, created_group, noti_message = handle_add_new_group(group_info, accountinfo_token)
        if error is not None:
            raise Exception(error)
        await global_connection_manager.send_message_notifications(
            s_schemas.MessageGET.model_validate(noti_message).model_dump(mode="json"))
        return "Done"

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/join")
async def join_group(group_id: uuid.UUID,
                     accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        existed, group = handle_check_existed_group(group_id)
        if existed:
            # //TODO: checking group visibility or group invitation notification, leave for later
            error, new_participant, joined_message = handle_add_new_participant(group_id, accountinfo_token.id,
                                                                                group_name=group.name,
                                                                                accountinfo_name=accountinfo_token.name,
                                                                                with_notification=True)
            if error is not None:
                raise Exception(error)
            await global_connection_manager.send_message_notifications(
                s_schemas.MessageGET.model_validate(joined_message).model_dump(mode="json"))

            return new_participant
        raise Exception("Group not found")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{group_id}/messages")
def get_message_list(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
                     group_id: uuid.UUID):
    if handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        message_list = s_models.MessageByGroup.objects.filter(group_id=group_id).all()
        return message_list[:]

    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You are not a participant of the group")


@router.get("/{group_id}/participants")
def get_group_participants(
        accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
        group_id: uuid.UUID):

    if handle_check_joined_participant(group_id, accountinfo_token.id)[0]:
        error, participant_list = handle_get_all_participants(group_id)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error)
        return participant_list

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="You are not a participant of the group")


@router.post("/{group_id}/participants/add")
async def add_group_participant(
        accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
        group_id: uuid.UUID, accountinfo_id: int):

    joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
    if not joined or participant.role == s_models.CONSTANT.Participant_role[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You don't have permission to add participant")
    with PostgresSession() as session:
        existed_user = session.scalar(select(p_models.Accountinfo).where(p_models.Accountinfo.id == accountinfo_id))
        if existed_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Participant account not found")
        error, participant, noti_message = handle_add_new_participant(group_id, accountinfo_id, accountinfo_name=existed_user.name, with_notification=True)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error)
        await global_connection_manager.send_message_notifications(
            s_schemas.MessageGET.model_validate(noti_message).model_dump(mode="json"))
        return participant


@router.delete("/{group_id}/participants/delete")
async def delete_group_participant(
        accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
        group_id: uuid.UUID, accountinfo_id: int):

    joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
    if not joined or participant.role in s_models.CONSTANT.Participant_role[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="You don't have permission to delete participant")
    error, left_noti_message = handle_remove_participant(group_id, accountinfo_id, with_notification=True)
    if error is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=error)
    await global_connection_manager.send_message_notifications(
        s_schemas.MessageGET.model_validate(left_noti_message).model_dump(mode="json"))
    return "Done"


@router.delete("/{group_id}/leave")
async def leave_group(group_id: uuid.UUID,
                      accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
        if not joined:
            raise Exception("You are not a participant of the group")
        existed, group = handle_check_existed_group(group_id, allow_private_groups=True)
        if not existed:
            raise Exception("Group not found")
        participant.delete()
        leave_group_message = s_models.MessageByGroup.create(group_id=group_id, accountinfo_id=accountinfo_token.id,
                                                             group_name=group.name,
                                                             accountinfo_name=accountinfo_token.name,
                                                             type=s_models.CONSTANT.Message_type[2],
                                                             content=f"User {accountinfo_token.name} has left group.")
        await global_connection_manager.send_message_notifications(
            s_schemas.MessageGET.model_validate(leave_group_message).model_dump(mode="json"))
        return "Done"

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.delete("/{group_id}/delete")
def delete_group(group_id: uuid.UUID,
                 accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
        if not joined:
            raise Exception("You are not a participant of the group")
        if participant.role in s_models.CONSTANT.Participant_role[0:2]:
            raise Exception("You don't have permission to delete group")
        # //TODO: delete all messages, participants, notifications, etc
        s_models.Group.objects.filter(id=group_id).first().delete()
        return "Done"
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.get("/{group_id}/info/get")
def get_group_info(group_id: uuid.UUID,
                   accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):

    try:
        joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
        if not joined:
            raise Exception("You are not a participant of the group")
        existed, group = handle_check_existed_group(group_id, allow_private_groups=True)
        if not existed:
            raise Exception("Group not found")
        return s_schemas.GroupGET.model_validate(group).model_dump()

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.post("/{group_id}/info/set")
def set_group_info(group_id: uuid.UUID,
                   new_group_info: s_schemas.GroupPOST,
                   accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
        if not joined:
            raise Exception("You are not a participant of the group")
        if participant.role == s_models.CONSTANT.Participant_role[0]:
            raise Exception("You don't have permission to edit info")

        group = s_models.Group.objects.filter(id=group_id).first()
        if group.name != new_group_info.name:
            pass  # //TODO: Add new group_by_name and remove old one

        group.update(**new_group_info.model_dump())
        return s_schemas.GroupGET.model_validate(group).model_dump()

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))
