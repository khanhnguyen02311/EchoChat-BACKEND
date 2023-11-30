from typing import Annotated
from fastapi import APIRouter, Depends
from components.functions.security import handle_renew_access_token, handle_get_current_accountinfo

router = APIRouter()


@router.post("/token/renew")
async def renew_token(result_access_token: Annotated[str, Depends(handle_renew_access_token)]):
    return {"access_token": result_access_token}


@router.post("/token/validate")
async def validate_token(token: str):
    accountinfo = handle_get_current_accountinfo(token)
    return accountinfo.id
