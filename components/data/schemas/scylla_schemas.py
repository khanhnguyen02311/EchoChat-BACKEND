import uuid
from datetime import datetime
from pydantic import constr
from . import BaseORMModel, BaseListModel
from ..models import scylla_models as s_models


class GroupGET(BaseORMModel):
    id: uuid.UUID
    name: str
    description: str | None
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


class MessageGET(BaseORMModel):
    group_id: uuid.UUID
    accountinfo_id: int
    content: constr(max_length=256)
    type: str
    group_name: str | None = None
    accountinfo_name: str | None = None
    time_created: datetime


class MessagePOST(BaseORMModel):
    group_id: uuid.UUID
    accountinfo_id: int | None = None
    content: constr(max_length=256)
    type: str = s_models.CONSTANT.Message_type[0]
    group_name: str | None = None
    accountinfo_name: str | None = None


class MessageMODIFY(BaseORMModel):
    group_id: uuid.UUID
    accountinfo_id: int | None = None
    time_created: datetime
