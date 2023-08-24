from typing import List, Optional
from pydantic import BaseModel, ConfigDict, constr
from . import postgres_models


class BaseORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TestingTableSchema(BaseORMModel):
    id: int
    item: str
    optional_item: Optional[str]
    number: int


class AddressSchema(BaseORMModel):
    id: int
    detail_address: str
    id_AccountInfo: int


class AccountInfoSchema(BaseORMModel):
    id: int
    name: str
    age: Optional[int]
    phone_number: Optional[str]
    id_Account: int


class AccountSchema(BaseORMModel):
    id: int
    username: str
    id_AccountInfo: int
    # rel_Addresses: List[AddressSchema]
