import uuid
from datetime import datetime
from typing import Any
from components.storages import ScyllaSession as session
from components.storages.models import scylla_models as s_models, postgres_models as p_models
from components.storages.schemas import scylla_schemas as s_schemas


def handle_check_joined_participant(group_id: uuid.UUID, accountinfo_id: int) -> \
        tuple[bool, s_models.ParticipantByGroup | None]:
    """Check if user already joined group. Return True/False result \n
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
                               time: datetime = datetime.utcnow(),
                               with_notification: bool = False) -> \
        tuple[Any, s_models.ParticipantByGroup | None]:
    """Handle adding new participant to group \n
    Return: (error, participant_item)"""

    # check if participant exists
    joined, _ = handle_check_joined_participant(group_id, accountinfo_id)
    if joined:
        return f"User {accountinfo_name} already existed in group", None

    new_participant_by_group = s_models.ParticipantByGroup.create(
        group_id=group_id,
        time_created=time,
        accountinfo_id=accountinfo_id,
        role=role
    )
    if with_notification:
        s_models.ParticipantByAccount.create(
            accountinfo_id=accountinfo_id,
            group_id=group_id,
            last_updated=time,
            role=role
        )
        s_models.MessageByGroup.create(
            group_id=group_id,
            accountinfo_id=accountinfo_id,
            group_name=group_name,
            accountinfo_name=accountinfo_name,
            type=s_models.CONSTANT.Message_type[2],
            content=f"User {accountinfo_name} has joined group."
        )
    return None, new_participant_by_group


def handle_create_new_group(group_info: s_schemas.GroupPOST, list_accountinfo: list[p_models.Accountinfo]) -> \
        tuple[Any, s_models.Group | None]:

    new_group = s_models.Group.create(**group_info.model_dump())
    error_list = []
    # group owner should be the first id in list
    error, _ = handle_add_new_participant(new_group.id, list_accountinfo[0].id,
                                          role=s_models.CONSTANT.Participant_role[2],
                                          group_name=group_info.name,
                                          accountinfo_name=list_accountinfo[0].name,
                                          with_notification=True)
    for accountinfo in list_accountinfo[1:]:
        error, _ = handle_add_new_participant(new_group.id, accountinfo.id, group_name=group_info.name,
                                              accountinfo_name=list_accountinfo[0].name, with_notification=True)
        if error is not None:
            error_list.append(error)

    return None if len(error_list) == 0 else error_list, new_group


def handle_get_personal_groups(accountinfo_id: int):
    participant_query = session.execute(
        f"select last_updated, group_id from participant_by_account where accountinfo_id={accountinfo_id} group by group_id")
    participant_query = sorted(participant_query, key=lambda query_row: query_row['last_updated'], reverse=True)

    message_list = []
    for row in participant_query:
        # group_query = session.execute(f"select * from group where id={row['group_id']}").one()
        group_last_message = session.execute(
            f"select * from message_by_group where group_id={row['group_id']} limit 1").one()
        message_list.append(group_last_message)

    return message_list


def handle_add_group_message(accountinfo_id, group_id, content):
    existed, participant = handle_check_joined_participant(group_id, accountinfo_id)
    if existed:
        new_message = s_models.MessageByGroup.create(text=content,
                                                     id_chatgroup=group_id,
                                                     id_chatparticipant=participant.accountinfo_id)
        return new_message
    return None
