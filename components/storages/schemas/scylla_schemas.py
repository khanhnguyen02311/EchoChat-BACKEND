import uuid
from datetime import datetime
from pydantic import conint, constr
from . import BaseORMModel, BaseListModel


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
    role: int
