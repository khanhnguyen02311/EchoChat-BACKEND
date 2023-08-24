from typing import Annotated

from fastapi import APIRouter, Depends
from components.functions.security import handle_get_current_user
from components.storages import postgres_models as p_models, postgres_schemas as p_schemas

router = APIRouter()


@router.get("/me")
async def getinfo(account: Annotated[p_models.Account, Depends(handle_get_current_user)]):
    return p_schemas.AccountSchema.model_validate(account).model_dump()
