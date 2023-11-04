from fastapi import APIRouter, HTTPException, status

from components.data import PostgresSession
from components.data.schemas import postgres_schemas as p_schemas
from components.functions.account import handle_create_account

router = APIRouter()


@router.post("/signup")
async def signup(account_signup: p_schemas.AccountPOST):
    with PostgresSession.begin() as session:
        error, account = handle_create_account(session, account_signup)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error)
        session.commit()

    return "Done"
