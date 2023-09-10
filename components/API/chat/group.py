from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from cassandra.cqlengine import connection
from components.functions.security import handle_get_current_user_oauth2
from components.functions.chat import handle_create_new_group
from components.storages import (postgres_schemas as p_schemas, postgres_models as p_models,
                                 scylla_models as s_models)

router = APIRouter(prefix="/group")


@router.get("/list")
def get_group_list(account: Annotated[p_models.Account, Depends(handle_get_current_user_oauth2)]):
    result_list = []
    list_group_participant = s_models.ChatParticipantByAccount.objects.filter(id_account=account.id).all()
    for i in list_group_participant:
        result_list.append(i.id_chatgroup)
    return result_list


@router.post("/create")
def create_new_group(data: p_schemas.AccountSchema,
                     account: Annotated[p_models.Account, Depends(handle_get_current_user_oauth2)]):
    try:
        created_group = handle_create_new_group([data.id, account.id])
        return created_group

    except Exception as e:
        return HTTPException(status_code=400, detail=str(e))
