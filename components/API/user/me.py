from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from components.data.DAOs import redis as d_redis
from components.functions.security import handle_get_current_account, handle_get_current_accountinfo
from components.functions.account import handle_edit_accountinfo, handle_edit_password
from components.data import PostgresSession
from pydantic import BaseModel
from components.data.schemas import postgres_schemas as p_schemas
from components.data.models import postgres_models as p_models

router = APIRouter(prefix="/me")

class ChangePasswordINPUT(BaseModel):
    old_password: str
    new_password: str

@router.get("/info/get")
def get_user_info(account_token: Annotated[p_models.Account, Depends(handle_get_current_account)]):
    error, accountinfo_cached = d_redis.get_user_info(account_token.accountinfo_id, "Accountinfo")
    if error is not None:
        print(error)
    if accountinfo_cached is not None:
        return {**p_schemas.AccountGET.model_validate(account_token).model_dump(),
                **p_schemas.AccountinfoGET.model_validate(accountinfo_cached).model_dump()}

    with PostgresSession() as session:
        accountinfo_query = select(p_models.Accountinfo).where(p_models.Accountinfo.id == account_token.accountinfo_id)
        accountinfo = session.scalar(accountinfo_query)
        if accountinfo is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accountinfo not found")
        d_redis.set_user_info(accountinfo, "Accountinfo")

    return {**p_schemas.AccountGET.model_validate(account_token).model_dump(),
            **p_schemas.AccountinfoGET.model_validate(accountinfo).model_dump()}


@router.post("/info/set")
def set_user_info(accountinfo_new: p_schemas.AccountinfoPUT,
                        accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    with PostgresSession.begin() as session:
        error = handle_edit_accountinfo(session, accountinfo_token, accountinfo_new)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
        session.commit()
    return "Done"


@router.post("/info/change-password")
def change_password(passwords: ChangePasswordINPUT, account_token: Annotated[p_models.Account, Depends(handle_get_current_account)]):
    with PostgresSession.begin() as session:
        error = handle_edit_password(session, account_token, passwords.old_password, passwords.new_password)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
        session.commit()
    return "Done"


@router.get("/avatar/get")
def get_user_avatar(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    pass


@router.post("/avatar/set")
def set_user_avatar(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    pass
