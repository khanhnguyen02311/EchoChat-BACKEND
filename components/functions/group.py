import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import select
from components.data import ScyllaSession, PostgresSession
from components.data.models import scylla_models as s_models, postgres_models as p_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas


def handle_check_existed_group(group_id: uuid.UUID,
                               allow_private_groups: bool = False) -> tuple[bool, s_models.Group | None]:
    """Check if group already existed\n
    Return: (result, group_item)"""

    existed_group = s_models.Group.objects.filter(id=group_id).first()
    if existed_group is None:
        return False, None
    if not allow_private_groups and existed_group.visibility is False:
        return False, None

    return True, existed_group


def handle_check_joined_participant(group_id: uuid.UUID, accountinfo_id: int) -> \
        tuple[bool, s_models.ParticipantByGroup | None]:
    """Check if user already joined group\n
    Return: (result, participant_item)"""

    participant = s_models.ParticipantByGroup.objects.filter(group_id=group_id).filter(
        accountinfo_id=accountinfo_id).allow_filtering().first()
    if participant is not None:
        return True, participant
    return False, None


def handle_add_new_participant(group_id: uuid.UUID,
                               accountinfo_id: int,
                               role: str = s_models.CONSTANT.Participant_role[0],
                               group_name: str = None,
                               accountinfo_name: str = None,
                               with_notification: bool = False) -> \
        tuple[Any, s_models.ParticipantByGroup | None, s_models.MessageByGroup | None]:
    """Handle adding new participant to group. Send back the joined event if needed\n
    Return: (error, participant_item, joined_message_item)"""

    # check if participant exists
    joined, _ = handle_check_joined_participant(group_id, accountinfo_id)
    if joined:
        return f"User {accountinfo_name} already existed in group", None, None

    new_participant_by_group = s_models.ParticipantByGroup.create(
        group_id=group_id,
        accountinfo_id=accountinfo_id,
        role=role
    )

    joined_group_message = None
    if with_notification:
        s_models.ParticipantByAccount.create(
            accountinfo_id=accountinfo_id,
            group_id=group_id,
            role=role
        )
        joined_group_message = s_models.MessageByGroup.create(
            group_id=group_id,
            accountinfo_id=accountinfo_id,
            group_name=group_name,
            accountinfo_name=accountinfo_name,
            type=s_models.CONSTANT.Message_type[2],
            content=f"User {accountinfo_name} has joined group."
        )

    return None, new_participant_by_group, joined_group_message


def handle_add_new_group(group_info: s_schemas.GroupPOST, accountinfo: p_models.Accountinfo,
                         with_creator_notification: bool = True) -> \
        tuple[Any, s_models.Group | None, s_models.MessageByGroup | None]:
    """Create new group and assign creator for that group. Return error if existed.\n
    Return: (error, group_item, notification_message)"""

    ## Add new group_by_name, if needed later ##
    new_group = s_models.Group.create(**group_info.model_dump())
    error_list = []
    # joined_messages = []
    # group owner should be the first id in list
    error, _, joined_message = handle_add_new_participant(new_group.id, accountinfo.id,
                                                          role=s_models.CONSTANT.Participant_role[2],
                                                          group_name=group_info.name,
                                                          accountinfo_name=accountinfo.name,
                                                          with_notification=with_creator_notification)
    return error, new_group, joined_message


def handle_get_personal_groups(accountinfo_id: int) -> list:
    """Get all joined groups and most recent messages\n
    Return: (message_list)"""

    participant_query = ScyllaSession.execute(
        f"select last_updated, group_id from participant_by_account where accountinfo_id={accountinfo_id} group by group_id")
    participant_query = sorted(participant_query, key=lambda query_row: query_row['last_updated'], reverse=True)

    message_list = []
    for row in participant_query:
        # group_query = session.execute(f"select * from group where id={row['group_id']}").one()
        group_last_message = ScyllaSession.execute(
            f"select * from message_by_group where group_id={row['group_id']} limit 1").one()
        message_list.append(group_last_message)

    return message_list


def handle_get_all_participants(group_id: uuid.UUID, with_accountinfo: bool = True) -> tuple[Any, list | None]:
    """Get all participants of a specified group. Can query with or without accountinfo\n
    Return: (error, result_list)"""

    existed, group = handle_check_existed_group(group_id, allow_private_groups=True)
    if not existed:
        return "Group not existed", None

    participant_list = s_models.ParticipantByGroup.objects.filter(group_id=group_id).all()
    if not with_accountinfo:
        return None, participant_list[:]

    result_list = []
    with PostgresSession.begin() as session:
        for row in participant_list:
            user_query = select(p_models.Accountinfo).where(p_models.Accountinfo.id == row.accountinfo_id)
            accountinfo = session.scalar(user_query)
            result_list.append(
                {**s_schemas.ParticipantPOST.model_validate(row).model_dump(),
                 **p_schemas.AccountinfoGET.model_validate(accountinfo).model_dump()})

    return None, result_list
