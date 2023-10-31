from datetime import datetime
from typing import List
from pydantic import BaseModel, conint, constr
from . import BaseORMModel, BaseListModel


class AccountLoginGET(BaseModel):
    username_or_email: str
    password: str


class AccountGET(BaseORMModel):
    # id: int
    # accountinfo_id: int
    username: str
    email: str


class AccountPOST(BaseORMModel):
    username: constr(max_length=128)
    password: constr(max_length=128)
    email: constr(max_length=128)


class AccountinfoGET(BaseORMModel):
    id: int
    name: str
    identifier: int
    description: str | None
    time_created: datetime
    accountattachment_id: int | None


class AccountinfoPUT(BaseORMModel):
    name: constr(max_length=64)
    identifier: conint(ge=0, le=9999)
    description: constr(max_length=128) | None = None


class ListAccountinfoGET(BaseListModel):
    root: List[AccountinfoGET]
