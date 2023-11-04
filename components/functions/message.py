import uuid
from datetime import datetime
from typing import Any
from components.data import ScyllaSession as session
from components.data.models import scylla_models as s_models, postgres_models as p_models
from components.data.schemas import scylla_schemas as s_schemas
from components.functions.group import handle_check_joined_participant


def handle_add_new_message(new_message: s_schemas.MessagePOST) -> tuple[Any, s_models.MessageByGroup | None]:
    """Add new message for provided account and group pair. Return error if needed. \n
    Return: (error, new_message)"""

    existed, participant = handle_check_joined_participant(new_message.group_id, new_message.accountinfo_id)
    if existed:
        s_models.MessageByAccount.create(**new_message.model_dump())
        new_message_by_group = s_models.MessageByGroup.create(**new_message.model_dump())
        return None, new_message_by_group
    return "You are not a participant of the group", None
