from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from components.storages import PostgresSession, postgres_models as p_models
from components.functions.account import handle_create_account, handle_create_account_info

router = APIRouter()


class InputSignup(BaseModel):
    email: str
    username: str
    password: str


@router.post("/signup")
async def signup(inputs: InputSignup):
    new_account = p_models.Account(**inputs.model_dump())
    with PostgresSession.begin() as session:
        try:
            error, account = handle_create_account(session, new_account)
            if error is not None:
                session.rollback()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return "Done"
