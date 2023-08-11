from fastapi import APIRouter
from pydantic import BaseModel

from components.storages import Session, postgres_models as p_models
from components.functions.account import handle_create_account, handle_create_account_info

router = APIRouter()


class InputSignup(BaseModel):
    email: str
    username: str
    password: str


@router.post("/signup")
async def signup(inputs: InputSignup):
    new_account = p_models.Account(**inputs.model_dump())
    with Session.begin() as session:
        try:
            new_account_info = handle_create_account_info(session)
            new_account.id_AccountInfo = new_account_info.id
            handle_create_account(session, new_account)
            session.commit()
        except Exception as e:
            session.rollback()
            return str(e)
    return "Done"
