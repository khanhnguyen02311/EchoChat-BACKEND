from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# from . import postgres_models


class BaseORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AccountinfoSchema(BaseORMModel):
    id: int
    name: str
    identifier: int
    description: str
    account_id: int


class AccountSchema(BaseORMModel):
    id: int
    username: str
    accountinfo_id: int
    time_created: datetime
    # rel_Addresses: List[AddressSchema]
