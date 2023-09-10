import uuid
from datetime import datetime
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.management import sync_table


# ==============================================================================
class TestTable(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    text = columns.Text()
    number = columns.Integer()
    time_created = columns.DateTime(default=datetime.utcnow)


# ==============================================================================
class ChatGroup(Model):
    id = columns.UUID(primary_key=True, default=uuid.uuid4)
    name = columns.Text(0, 128)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)


# ==============================================================================
class ChatParticipantByAccount(Model):
    id = columns.UUID(default=uuid.uuid4)
    notify = columns.Boolean()

    id_account = columns.Integer(primary_key=True)
    id_chatgroup = columns.UUID(primary_key=True, clustering_order="DESC")


# ==============================================================================
class ChatParticipantByChatGroup(Model):
    id = columns.UUID(default=uuid.uuid4)
    notify = columns.Boolean()

    id_chatgroup = columns.UUID(primary_key=True)
    id_account = columns.Integer(primary_key=True, clustering_order="DESC")


# ==============================================================================
class ChatMessage(Model):
    id = columns.UUID(default=uuid.uuid4)
    text = columns.Text(0, 512)
    id_chatgroup = columns.UUID(primary_key=True)
    time_created = columns.DateTime(primary_key=True, clustering_order="DESC", default=datetime.utcnow)
    id_chatparticipant = columns.UUID(primary_key=True)


# ==============================================================================
def sync_tables():
    sync_table(TestTable)
    sync_table(ChatGroup)
    sync_table(ChatParticipantByAccount)
    sync_table(ChatParticipantByChatGroup)
    sync_table(ChatMessage)
