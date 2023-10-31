import uuid
from datetime import datetime
from pydantic import constr
from . import BaseORMModel, BaseListModel
from ..models import scylla_models as s_models


class GroupGET(BaseORMModel):
    name: str
    description: str
    visibility: bool
    time_created: datetime


class GroupPOST(BaseORMModel):
    name: constr(max_length=64)
    description: constr(max_length=128) | None = None
    visibility: bool = True


class ParticipantGET(BaseORMModel):
    accountinfo_id: int
    group_id: uuid.UUID
    last_updated: datetime
    notify: bool
    role: str


class ParticipantPOST(BaseORMModel):
    group_id: uuid.UUID
    accountinfo_id: int
    role: str = s_models.CONSTANT.Participant_role[0]


class MessagePOST(BaseORMModel):
    group_id: uuid.UUID
    accountinfo_id: int | None = None
    content: constr(max_length=256)
    type: str = s_models.CONSTANT.Message_type[0]
    group_name: str | None = None
    accountinfo_name: str | None = None


class MessageGET(BaseORMModel):
    group_id: uuid.UUID
    accountinfo_id: int
    content: constr(max_length=256)
    type: str
    group_name: str | None = None
    accountinfo_name: str | None = None
    time_created: datetime
