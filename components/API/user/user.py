from typing import Annotated

from fastapi import APIRouter, Depends
from components.functions.security import handle_get_current_user_oauth2
from components.storages import postgres_models as p_models, postgres_schemas as p_schemas
from components.storages import PostgresSession
from components.storages.postgres_models import Accountinfo

router = APIRouter()


@router.get("/me")
async def get_info(accountinfo: Annotated[p_models.Account, Depends(handle_get_current_user_oauth2)]):
    return p_schemas.AccountinfoSchema.model_validate(accountinfo).model_dump()


@router.post("/edit/name")
async def edit_name(accountinfo: Annotated[p_models.Account, Depends(handle_get_current_user_oauth2)]):
    with PostgresSession.begin() as session:
        pass
