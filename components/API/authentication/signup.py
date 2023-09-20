from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from components.storages import PostgresSession, postgres_models as p_models
from components.functions.account import handle_create_account

router = APIRouter()


class InputSignup(BaseModel):
    email: str
    username: str
    password: str


@router.post("/signup")
async def signup(inputs: InputSignup):
    new_account = p_models.Account(**inputs.model_dump())
    with PostgresSession.begin() as session:
        error, account = handle_create_account(session, new_account)
        if error is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=error)
        session.commit()

    return "Done"
