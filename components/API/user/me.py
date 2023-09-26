from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from components.functions.security import handle_get_current_user_oauth2
from components.functions.account import handle_edit_accountinfo
from components.storages import PostgresSession, postgres_models as p_models, postgres_schemas as p_schemas

router = APIRouter()


@router.get("/me/info")
async def get_info(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_user_oauth2)]):
    return p_schemas.AccountinfoSchema.model_validate(token_account).model_dump()


@router.post("/me/edit")
async def edit_user(accountinfo_new: p_schemas.AccountinfoSchemaPUT,
                    token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_user_oauth2)]):
    with PostgresSession.begin() as session:
        error = handle_edit_accountinfo(session, token_account, accountinfo_new)
        if error is not None:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)
        session.commit()
        return "Done"


@router.post("/me/avatar/set")
async def set_avatar(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_user_oauth2)]):
    pass


@router.get("/me/avatar/get")
async def get_avatar(token_account: Annotated[p_models.Accountinfo, Depends(handle_get_current_user_oauth2)]):
    pass
