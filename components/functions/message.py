import uuid
from datetime import datetime
from typing import Any
from cassandra.query import SimpleStatement
from configurations.conf import Proto
from components.data import ScyllaSession as session
from components.data.models import scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas
from components.services.rabbitmq.services_rabbitmq import RabbitMQService


def handle_get_messages_from_group(group_id: uuid.UUID, before_time: datetime | None = None) -> list:
    """Get messages from group\n
    Return: (message_list)"""

    if before_time is None:
        before_time = datetime.utcnow()
    message_lookup_stmt = SimpleStatement(f"select * from message_by_group where group_id=%s and time_created<%s limit 10")
    messages = session.execute(message_lookup_stmt, [group_id, before_time])
    return messages


def handle_add_new_message(new_message: s_schemas.MessagePOST) -> \
        tuple[Any, s_models.MessageByGroup | None]:
    """Add new message for provided account and group pair. Return error if needed. \n
    Return: (error, new_message)"""

    try:
        s_models.MessageByAccount.create(**new_message.model_dump())
        new_message_by_group = s_models.MessageByGroup.create(**new_message.model_dump())
        RabbitMQService.send_data(routing=Proto.RMQ_ROUTING_KEY_MSG,
                                  data=s_schemas.MessageGET.model_validate(new_message_by_group).model_dump_json())
        return None, new_message_by_group
    except Exception as e:
        return str(e), None


def handle_remove_message(message: s_schemas.MessageMODIFY, accountinfo_id: int) -> Any:
    """Remove message for provided account and group pair. Return error if needed. \n
    Return: (error, new_message)"""

    try:
        existed_message_by_group = s_models.MessageByGroup.objects \
            .filter(group_id=message.group_id) \
            .filter(time_created=message.time_created) \
            .filter(accountinfo_id=accountinfo_id).first()
        if message is None:
            return "Message not existed or not belong to this account"

        existed_message_by_group.delete()
        s_models.MessageByAccount.objects.filter(group_id=message.group_id) \
            .filter(time_created=message.time_created) \
            .filter(accountinfo_id=accountinfo_id).delete()
        return None
    except Exception as e:
        return str(e)


def handle_get_pinned_messages(group_id: uuid.UUID) -> list:
    """Get pinned messages from group\n
    Return: (message_list)"""

    pinned_messages = s_models.MessagePinned.objects.filter(group_id=group_id).all()
    return pinned_messages


def handle_pin_message(message: s_schemas.MessageMODIFY) -> tuple[Any, s_models.MessageByGroup | None]:
    """Pin message for provided account and group pair. Return error if needed. \n
    Return: (error, new_message)"""

    try:
        existed_message_by_group = s_models.MessageByGroup.objects \
            .filter(group_id=message.group_id) \
            .filter(time_created=message.time_created) \
            .filter(accountinfo_id=message.accountinfo_id).first()
        if existed_message_by_group is None:
            return "Message not found", None
        s_models.MessagePinned.create(**s_schemas.MessageGET.model_validate(existed_message_by_group).model_dump())
        return None, existed_message_by_group

    except Exception as e:
        return str(e), None


def handle_unpin_message(message: s_schemas.MessageMODIFY) -> tuple[Any, s_schemas.MessageGET | None]:
    """Unpin message for provided account and group pair. Return error if needed. \n
    Return: (error, new_message)"""

    try:
        existed_message_pinned = s_models.MessagePinned.objects \
            .filter(group_id=message.group_id) \
            .filter(time_created=message.time_created) \
            .filter(accountinfo_id=message.accountinfo_id).first()
        if existed_message_pinned is None:
            return "Message not found", None
        message = s_schemas.MessageGET.model_validate(existed_message_pinned)
        existed_message_pinned.delete()
        return None, message

    except Exception as e:
        return str(e), None
