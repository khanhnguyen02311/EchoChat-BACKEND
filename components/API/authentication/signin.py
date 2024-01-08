from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import components.data.schemas.postgres_schemas as p_schemas
from components.functions.account import handle_authenticate_account
from components.functions.security import handle_create_access_token, handle_create_refresh_token
from components.data import PostgresSession

router = APIRouter()


@router.post("/signin")
async def signin(data: p_schemas.AccountLoginGET):
    with PostgresSession.begin() as session:
        error, user = handle_authenticate_account(session,
                                                  username_or_email=data.username_or_email,
                                                  password=data.password)
        if error is not None:
            session.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )

        return {
            "access_token": handle_create_access_token(user),
            "refresh_token": handle_create_refresh_token(user)
        }
