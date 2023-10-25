from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from components.functions.security import handle_get_current_account, handle_get_current_accountinfo
from components.functions.account import handle_edit_accountinfo
from components.storages import PostgresSession
from components.storages.schemas import postgres_schemas as p_schemas
from components.storages.models import postgres_models as p_models

router = APIRouter()


@router.get("/me/info/get")
async def get_info(account_token: Annotated[p_models.Account, Depends(handle_get_current_account)]):
    print(account_token.accountinfo_id)
    with PostgresSession() as session:
        accountinfo_query = select(p_models.Accountinfo).where(p_models.Accountinfo.id == account_token.accountinfo_id)
        accountinfo = session.scalar(accountinfo_query)
        if accountinfo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account info not found")

    return {**p_schemas.AccountSchemaGET.model_validate(account_token).model_dump(),
            **p_schemas.AccountinfoSchemaGET.model_validate(accountinfo).model_dump()}


@router.post("/me/info/set")
async def edit_user(accountinfo_new: p_schemas.AccountinfoSchemaPUT,
                    accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    with PostgresSession.begin() as session:
        error = handle_edit_accountinfo(session, accountinfo_token, accountinfo_new)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
        session.commit()
        return "Done"


@router.get("/me/avatar/get")
async def get_avatar(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    pass


@router.post("/me/avatar/set")
async def set_avatar(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    pass
