import uuid
from datetime import datetime
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.management import sync_table


# ==============================================================================
class Chatgroup(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    display_name = columns.Text(0, 128)
    visibility = columns.Boolean(default=True)
    time_created = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
class ChatgroupByName(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    name = columns.Text(0, 128)
    time_created = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
class ChatparticipantByAccount(Model):
    id_account = columns.Integer(primary_key=True)
    id_chatgroup = columns.UUID(primary_key=True, clustering_order="ASC")


# ==============================================================================
class ChatparticipantByChatgroup(Model):
    id = columns.UUID(default=uuid.uuid4)
    notify = columns.Boolean()

    id_chatgroup = columns.UUID(primary_key=True)
    id_account = columns.Integer(primary_key=True, clustering_order="DESC")


# ==============================================================================
class Chatmessage(Model):
    id = columns.UUID(default=uuid.uuid4)
    text = columns.Text(0, 512)
    id_chatgroup = columns.UUID(primary_key=True)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)
    id_chatparticipant = columns.UUID(primary_key=True)


# ==============================================================================
def sync_tables():
    # sync_table(ChatGroup)
    # sync_table(ChatParticipantByAccount)
    # sync_table(ChatParticipantByChatGroup)
    # sync_table(ChatMessage)
    pass
