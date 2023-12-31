import uuid
from datetime import datetime
from typing import Any
from cassandra.query import SimpleStatement
from sqlalchemy import select
from components.data import ScyllaSession, PostgresSession
from components.data.models import scylla_models as s_models, postgres_models as p_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas
from components.data.DAOs import redis as d_redis


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
        tuple[bool, s_models.ParticipantByAccount | None]:
    """Check if user already joined group\n
    Return: (result, participant_item)"""

    participant = s_models.ParticipantByAccount.objects. \
        filter(group_id=group_id).filter(accountinfo_id=accountinfo_id).first()
    if participant is None:
        return False, None
    
    return True, participant


def handle_add_new_participant(group_id: uuid.UUID,
                               accountinfo_id: int,
                               role: str = s_models.CONSTANT.Participant_role[0],
                               accountinfo_name: str = None) -> tuple[Any, s_models.ParticipantByGroup | None]:
    """Handle adding new participant to group\n
    Return: (error, participant_item)"""

    # check if participant exists
    participant = s_models.ParticipantByAccount.objects.filter(group_id=group_id).filter(accountinfo_id=accountinfo_id).first()
    if participant is not None:
        return f"User {accountinfo_name} already existed in group", None
    time_now = datetime.utcnow()
    new_participant_by_group = s_models.ParticipantByGroup.create(group_id=group_id,
                                                                  accountinfo_id=accountinfo_id,
                                                                  role=role,
                                                                  time_created=time_now)
    s_models.ParticipantByAccount.create(accountinfo_id=accountinfo_id,
                                         group_id=group_id,
                                         role=role,
                                         time_created=time_now)
    return None, new_participant_by_group


def handle_remove_participant(group_id: uuid.UUID, accountinfo_id: int, with_accountinfo=False) -> tuple[Any, p_models.Accountinfo | None]:
    """Handle removing participant from group. Return error if needed\n"""

    existed_participant_by_account = s_models.ParticipantByAccount.objects \
        .filter(group_id=group_id).filter(accountinfo_id=accountinfo_id).first()
    if existed_participant_by_account is None:
        return "User not existed in group", None
    if existed_participant_by_account.role == s_models.CONSTANT.Participant_role[2]:
        return "Cannot remove creator from group", None

    accountinfo = None
    if with_accountinfo:
        with PostgresSession.begin() as session:
            accountinfo = session.scalar(select(p_models.Accountinfo).where(p_models.Accountinfo.id == accountinfo_id))
            session.expunge(accountinfo)
    existed_participant_by_group = s_models.ParticipantByGroup.objects \
        .filter(group_id=group_id).filter(time_created=existed_participant_by_account.time_created).filter(accountinfo_id=accountinfo_id).first()
    if existed_participant_by_group is not None:
        existed_participant_by_group.delete()
    existed_participant_by_account.delete()
    return None, accountinfo


def handle_add_new_group(group_info: s_schemas.GroupPOST, accountinfo: p_models.Accountinfo) -> \
        tuple[Any, s_models.Group | None]:
    """Create new group and assign creator for that group. Return error if existed.\n
    Return: (error, group_item)"""

    ## Add new group_by_name, if needed later ##
    new_group = s_models.Group.create(**group_info.model_dump())
    error, _ = handle_add_new_participant(new_group.id, accountinfo.id,
                                          role=s_models.CONSTANT.Participant_role[2],
                                          accountinfo_name=accountinfo.name)
    return error, new_group


def handle_get_recent_groups(accountinfo_id: int, before_time: datetime | None = None) -> list:
    """Get joined groups and their most recent messages\n
    Return: (message_list)"""

    if before_time is None:
        before_time = datetime.utcnow()
    paging_state = None
    recent_groups_lookup_stmt = SimpleStatement("select group_id from notification where accountinfo_id=%s and type=%s and time_created<%s", fetch_size=25)
    message_lookup_stmt = SimpleStatement("select * from message_by_group where group_id=%s")

    existed_group = {}
    message_list = []
    while len(existed_group) < 10:  # at least 10 groups at a time
        if paging_state:
            result_set = ScyllaSession.execute(recent_groups_lookup_stmt, (accountinfo_id, s_models.CONSTANT.Notification_type[0], before_time), paging_state=paging_state)
        else:
            result_set = ScyllaSession.execute(recent_groups_lookup_stmt, (accountinfo_id, s_models.CONSTANT.Notification_type[0], before_time))
        paging_state = result_set.paging_state
        rows = result_set.current_rows
        for row in rows:
            if row["group_id"] not in existed_group:
                group = ScyllaSession.execute(message_lookup_stmt, [row["group_id"]]).one()
                existed_group[row["group_id"]] = True
                message_list.append(group)
        if paging_state is None:  # no more data rows
            break
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
            error, cached_user = d_redis.get_user_info(row.accountinfo_id, "Accountinfo")
            if error is not None:
                print(error)
            if cached_user is not None:
                result_list.append({**s_schemas.ParticipantPOST.model_validate(row).model_dump(),
                                    **p_schemas.AccountinfoGET.model_validate(cached_user).model_dump()})
                continue
            user_query = select(p_models.Accountinfo).where(p_models.Accountinfo.id == row.accountinfo_id)
            accountinfo = session.scalar(user_query)
            d_redis.set_user_info(accountinfo, "Accountinfo")
            result_list.append(
                {**s_schemas.ParticipantPOST.model_validate(row).model_dump(),
                 **p_schemas.AccountinfoGET.model_validate(accountinfo).model_dump()})

    return None, result_list
