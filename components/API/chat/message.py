import json
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from components.functions.security import handle_get_current_accountinfo
from components.functions.group import handle_add_new_group, handle_get_personal_groups, handle_add_new_participant, \
    handle_check_joined_participant, handle_check_existed_group, handle_get_all_participants
from components.data import PostgresSession
from components.data.models import postgres_models as p_models, scylla_models as s_models
from components.data.schemas import scylla_schemas as s_schemas, postgres_schemas as p_schemas
from components.utilities.connection_manager import global_connection_manager

router = APIRouter(prefix="/message")


@router.post("/new")
def add_new_message(accountinfo_token: Annotated[p_models.Accountinfo, Depends(handle_get_current_accountinfo)]):
    pass
