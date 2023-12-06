import uuid
from datetime import datetime
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.management import sync_table


# ==============================================================================
class CONSTANT:
    Participant_role = ["Participant", "Admin", "Creator"]
    Message_type = ["Message", "File", "Event", "Other"]
    Groupattachment_type = ["Message", "Group"]
    Notification_type = ["NewMessage", "GroupRequest", "Others"]


# ==============================================================================
class Group(Model):
    """Store info, used for normal group operations \n
    - Primary key: (id)"""

    id = columns.UUID(primary_key=True, default=uuid.uuid1)

    name = columns.Text(max_length=64, required=True)
    description = columns.Text(max_length=128)
    visibility = columns.Boolean(default=True)
    time_created = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
class GroupByName(Model):
    """Store visible group info, used for searching groups by name \n
    Primary key: \n ((name), id) \n
    with id DESC"""

    name = columns.Text(primary_key=True, max_length=64)
    id = columns.UUID(primary_key=True, clustering_order="DESC", default=uuid.uuid1)

    description = columns.Text(max_length=128)
    time_created = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
class ParticipantByAccount(Model):
    """Store participant info, use for querying latest group activities of specific account \n
    Primary key: \n ((accountinfo_id), group_id, time_created) \n
    with group_id DESC, last_updated DESC"""

    accountinfo_id = columns.Integer(primary_key=True)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)  # updated from last_updated to time_created
    group_id = columns.UUID(primary_key=True, clustering_order="DESC")

    notify = columns.Boolean(default=True)
    role = columns.Text(max_length=15, default=CONSTANT.Participant_role[0])


# ==============================================================================
class ParticipantByGroup(Model):
    """Store participant info, used for getting participant list and notification-based operations \n
    Primary key: \n ((group_id), time_created) \n
    with time_created DESC"""

    group_id = columns.UUID(primary_key=True)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)
    accountinfo_id = columns.Integer(primary_key=True, clustering_order="DESC")

    notify = columns.Boolean(default=True)
    role = columns.Text(max_length=15, default=CONSTANT.Participant_role[0])


# ==============================================================================
class MessageByAccount(Model):
    """Store messages sorted by account, used for user history and related things \n
    Primary key: \n ((accountinfo_id), time_created) \n
    with time_created DESC"""

    accountinfo_id = columns.Integer(primary_key=True)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)
    group_id = columns.UUID(primary_key=True, clustering_order="DESC")

    group_name = columns.Text(max_length=64)
    accountinfo_name = columns.Text(max_length=64)
    type = columns.Text(max_length=15, default=CONSTANT.Message_type[0])
    content = columns.Text(max_length=256, required=True)


# ==============================================================================
class MessageByGroup(Model):
    """Store messages sorted by group, used for querying group messages \n
    Primary key: \n ((group_id), time_created) \n
    with time_created DESC"""

    group_id = columns.UUID(primary_key=True)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)
    accountinfo_id = columns.Integer(primary_key=True, clustering_order="DESC")

    accountinfo_name = columns.Text(max_length=64)
    group_name = columns.Text(max_length=64)
    type = columns.Text(max_length=15, default=CONSTANT.Message_type[0])
    content = columns.Text(max_length=256, required=True)


# ==============================================================================
class MessagePinned(Model):
    """Store pinned messages sorted by group, used for message pinning operations \n
    Primary key: \n ((group_id), time_created) \n
    with time_created DESC"""

    group_id = columns.UUID(primary_key=True)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)
    accountinfo_id = columns.Integer(primary_key=True, clustering_order="DESC")

    accountinfo_name = columns.Text(max_length=64)
    group_name = columns.Text(max_length=64)
    type = columns.Text(max_length=15, default=CONSTANT.Message_type[0])
    content = columns.Text(max_length=256, required=True)
    time_pinned = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
class Groupattachment(Model):
    """Store group attachment info, used for normal file operations \n
    Primary key: \n ((group_id), type, filename) \n
    with type DESC, filename DESC"""

    group_id = columns.UUID(primary_key=True)
    type = columns.Text(primary_key=True, clustering_order="DESC",
                        max_length=15, default=CONSTANT.Groupattachment_type[0])
    filename = columns.Text(primary_key=True, clustering_order="DESC")

    time_created = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
class Notification(Model):
    """Store all notifications based on notification type \n
    Primary key: \n ((accountinfo_id), type, time_created, group_id) \n
    with time_created DESC, group_id DESC"""

    accountinfo_id = columns.Integer(primary_key=True)
    type = columns.Text(primary_key=True, max_length=15, default=CONSTANT.Notification_type[0])
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)
    group_id = columns.UUID(primary_key=True, clustering_order="DESC")

    accountinfo_id_sender = columns.Integer(required=True)
    content = columns.Text(max_length=256, required=True)


# ==============================================================================
class NotificationSeen(Model):
    """Store notifications seen by account \n
    Primary key: \n ((accountinfo_id), type, group_id, time_created) \n
    with type ASC, group_id DESC, time_created DESC"""

    accountinfo_id = columns.Integer(primary_key=True)
    type = columns.Text(primary_key=True, max_length=15, default=CONSTANT.Notification_type[0])
    group_id = columns.UUID(primary_key=True, clustering_order="DESC")
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)

    content = columns.Text(max_length=256, required=True)
    time_seen = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
def sync_tables():
    sync_table(Group)
    sync_table(GroupByName)
    sync_table(Groupattachment)
    sync_table(ParticipantByGroup)
    sync_table(ParticipantByAccount)
    sync_table(MessageByGroup)
    sync_table(MessageByAccount)
    sync_table(MessagePinned)
    sync_table(Notification)
    sync_table(NotificationSeen)
