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
    description: str | None


class AccountinfoSchemaPUT(BaseORMModel):
    name: str
    identifier: int
    description: str


class AccountSchemaGET(BaseORMModel):
    id: int
    username: str
    accountinfo_id: int
    time_created: datetime


class AccountSchemaPOST(BaseORMModel):
    username: str
    password: str
    email: str
