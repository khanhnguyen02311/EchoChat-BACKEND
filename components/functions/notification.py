import uuid
from datetime import datetime
from typing import Any
from cassandra.query import SimpleStatement, PreparedStatement
from components.data import ScyllaSession
from components.data.models import scylla_models as s_models, postgres_models as p_models
from components.data.schemas import scylla_schemas as s_schemas
from components.services.rabbitmq.services_rabbitmq import RabbitMQService
from configurations.conf import Proto


def handle_add_new_notification(notification: s_schemas.NotificationPOST) -> \
        tuple[Any, s_models.Notification | None]:
    """Create new notification for provided account and group pair. Return error if needed. \n
    Return: (error, new_notification)"""
    try:
        new_notification = s_models.Notification.create(**notification.model_dump())
        RabbitMQService.send_data(routing=Proto.RMQ_ROUTING_KEY_NOTI, data=new_notification)
        return None, new_notification
    except Exception as e:
        return str(e), None


def handle_check_seen_notification(accountinfo_id: int, group_id: uuid.UUID, notification_type: str, last_message_time: datetime) -> \
        tuple[bool, s_models.NotificationSeen | None]:
    """Check if notification is seen (most recent seen notification is after the specified time) \n
    Return: (result, notification_seen_item)"""

    notification_seen = s_models.NotificationSeen.objects \
        .filter(accountinfo_id=accountinfo_id) \
        .filter(type=notification_type) \
        .filter(group_id=group_id).first()
    if notification_seen is not None and notification_seen.time_created >= last_message_time:
        return True, notification_seen
    return False, None

# def handle_get_list_message_notifications(accountinfo_id: int, min_amount: int, time_before: datetime | None = None) -> list:
#     """Get joined groups and most recent messages\n
#     Return: (message_list)"""
#
#     if time_before is None:
#         time_before = datetime.utcnow()
#     paging_state = None
#     noti_lookup_stmt = SimpleStatement(f"select * from notification where accountinfo_id=%s " +
#                                        f"and type={s_models.CONSTANT.Message_type[0]} " +
#                                        "and time_created<%s", fetch_size=50)
#
#     group_lookup_stmt = ScyllaSession.prepare(f"select * from message_by_group where group_id=%s")
#
#     existed_groups = {}
#     message_list = []
#     while len(existed_groups) < min_amount:
#         rows = ScyllaSession.execute(noti_lookup_stmt, (accountinfo_id, time_before), paging_state=paging_state)
#         paging_state = rows.paging_state
#         for row in rows:
#             if row["group_id"] not in existed_groups:
#                 # get group info
#                 group = ScyllaSession.execute(group_lookup_stmt, [row["group_id"]]).one()
#                 existed_groups[row["group_id"]] = True
#                 # get seen status
#                 result, _ = handle_check_seen_notification(accountinfo_id, row["group_id"], row["time_created"])
#                 group["message_seen"] = result
#                 group["message"] = row["content"]
#                 message_list.append(group)
#
#         if paging_state is None:  # no more data rows
#             break
#
#     return message_list
