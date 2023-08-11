from fastapi import APIRouter
from pydantic import BaseModel

from components.storages import Session, postgres_schemas as p_schemas, postgres_models as p_models
from components.functions.account import handle_create_account

router = APIRouter()


class InputSignin(BaseModel):
    username_or_email: str
    password: str


@router.post("/signin")
async def signin(inputs: InputSignin):
    
    new_account = p_models.Account()
    with Session.begin() as session:
        try:
            handle_create_account(session, new_account)
            session.commit()
        except Exception as e:
            session.rollback()
            return str(e)
    return "Done"
