from datetime import datetime
from typing import List
from pydantic import BaseModel, RootModel, ConfigDict, conint, constr


class BaseORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseListModel(RootModel):
    root: List[BaseORMModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class AccountinfoSchemaGET(BaseORMModel):
    id: int
    name: str
    identifier: int
    description: str | None
    time_created: datetime
    accountattachment_id: int | None


class ListAccountinfoSchemaGET(BaseListModel):
    root: List[AccountinfoSchemaGET]


class AccountinfoSchemaPUT(BaseORMModel):
    name: constr(max_length=64)
    identifier: conint(ge=0, le=9999)
    description: constr(max_length=128) | None


class AccountSchemaGET(BaseORMModel):
    # id: int
    # accountinfo_id: int
    username: str
    email: str


class AccountSchemaPOST(BaseORMModel):
    username: constr(max_length=128)
    password: constr(max_length=128)
    email: constr(max_length=128)
