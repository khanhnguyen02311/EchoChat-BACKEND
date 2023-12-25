import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from components.functions.security import handle_get_current_accountinfo
from components.functions.group import handle_add_new_group, handle_get_recent_groups, handle_add_new_participant, \
    handle_check_joined_participant, handle_check_existed_group, handle_get_all_participants, handle_remove_participant
from components.functions.message import handle_add_new_message
from components.functions.notification import handle_check_seen_notification
from components.data import PostgresSession
from components.data.models import postgres_models as p_models, scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas

router = APIRouter(prefix="/group")


@router.get("/recent")
def get_recent_groups(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)], before_time: str | None = None):
    try:
        formatted_time = datetime.strptime(before_time, "%Y-%m-%dT%H:%M:%S.%f") if before_time is not None else None
        recent_list = handle_get_recent_groups(accountinfo_token.id, before_time=formatted_time)
        for message in recent_list:
            # get seen status
            message["seen_status"] = handle_check_seen_notification(accountinfo_token.id,
                                                                    message["group_id"],
                                                                    s_models.CONSTANT.Notification_type[0],
                                                                    message["time_created"])[0]
        return recent_list
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


@router.post("/create")
def create_new_group(group_info: s_schemas.GroupPOST,
                     accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        error, created_group = handle_add_new_group(group_info, accountinfo_token)
        if error is not None:
            raise Exception(error)
        error, _ = handle_add_new_message(s_schemas.MessagePOST(group_id=created_group.id,
                                                                accountinfo_id=accountinfo_token.id,
                                                                group_name=created_group.name,
                                                                accountinfo_name=accountinfo_token.name,
                                                                type=s_models.CONSTANT.Message_type[2],
                                                                content=f"User {accountinfo_token.name} has created group."))
        if error is not None:
            raise Exception(error)
        return created_group

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/join")
def join_group(group_id: uuid.UUID,
               accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        existed, group = handle_check_existed_group(group_id)
        if not existed:
            raise Exception("Group not found")
        # TODO: checking group visibility or group invitation notification, leave for later
        error, new_participant = handle_add_new_participant(group_id, accountinfo_token.id,
                                                            accountinfo_name=accountinfo_token.name)
        if error is not None:
            raise Exception(error)
        error, _ = handle_add_new_message(s_schemas.MessagePOST(group_id=group.id,
                                                                accountinfo_id=accountinfo_token.id,
                                                                group_name=group.name,
                                                                accountinfo_name=accountinfo_token.name,
                                                                type=s_models.CONSTANT.Message_type[2],
                                                                content=f"User {accountinfo_token.name} has joined group."))
        if error is not None:
            raise Exception(error)
        return new_participant

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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

    existed, group = handle_check_existed_group(group_id, allow_private_groups=True)
    if not existed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
    if not joined or participant.role == s_models.CONSTANT.Participant_role[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have permission to add participant")

    with PostgresSession() as session:
        existed_user = session.scalar(select(p_models.Accountinfo).where(p_models.Accountinfo.id == accountinfo_id))
        if existed_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Participant account not found")
        error, participant = handle_add_new_participant(group_id, accountinfo_id, accountinfo_name=existed_user.name)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error)
        error, _ = handle_add_new_message(s_schemas.MessagePOST(group_id=group.id,
                                                                accountinfo_id=accountinfo_token.id,
                                                                group_name=group.name,
                                                                accountinfo_name=accountinfo_token.name,
                                                                type=s_models.CONSTANT.Message_type[2],
                                                                content=f"User {accountinfo_token.name} added {existed_user.name} to the group."))
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error)
        return participant


@router.delete("/{group_id}/participants/delete")
async def delete_group_participant(
        accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)],
        group_id: uuid.UUID, accountinfo_id: int):

    existed, group = handle_check_existed_group(group_id, allow_private_groups=True)
    if not existed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    joined, participant = handle_check_joined_participant(group_id, accountinfo_token.id)
    if not joined or participant.role in s_models.CONSTANT.Participant_role[0]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have permission to delete participant")

    error, deleted_user = handle_remove_participant(group_id, accountinfo_id, with_accountinfo=True)
    if error is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=error)
    error, _ = handle_add_new_message(
        s_schemas.MessagePOST(group_id=group.id,
                              accountinfo_id=accountinfo_token.id,
                              group_name=group.name,
                              accountinfo_name=accountinfo_token.name,
                              type=s_models.CONSTANT.Message_type[2],
                              content=f"User {accountinfo_token.name} removed {deleted_user.name if deleted_user is not None else 'a participant'} from the group."))
    if error is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=error)
    return "Done"


@router.delete("/{group_id}/leave")
async def leave_group(group_id: uuid.UUID,
                      accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    try:
        existed, group = handle_check_existed_group(group_id, allow_private_groups=True)
        if not existed:
            raise Exception("Group not found")
        error, _ = handle_remove_participant(group_id, accountinfo_token.id)
        if error is not None:
            raise Exception(error)
        error, _ = handle_add_new_message(s_schemas.MessagePOST(group_id=group.id,
                                                                accountinfo_id=accountinfo_token.id,
                                                                group_name=group.name,
                                                                accountinfo_name=accountinfo_token.name,
                                                                type=s_models.CONSTANT.Message_type[2],
                                                                content=f"User {accountinfo_token.name} left group."))
        if error is not None:
            raise Exception(error)
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
