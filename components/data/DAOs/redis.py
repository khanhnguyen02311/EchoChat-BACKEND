from typing import Any

from components.data import RedisSession
from configurations.conf import Env
from components.data.models import postgres_models as p_models
from components.data.schemas import postgres_schemas as p_schemas


def get_user_info(account_id: int, account_type: str = "Account") -> tuple[Any, p_models.Account | p_models.Accountinfo | None]:
    cached_data = RedisSession.get(f"{account_type}:{account_id}")
    if cached_data is None:
        return None, None
    try:
        if account_type == "Account":
            data_from_schema = p_schemas.AccountGETALL.model_validate_json(cached_data)
            account_data = p_models.Account(**data_from_schema.model_dump())
        elif account_type == "Accountinfo":
            data_from_schema = p_schemas.AccountinfoGET.model_validate_json(cached_data)
            account_data = p_models.Accountinfo(**data_from_schema.model_dump())
        else:
            return "Invalid account type", None
    except Exception as e:
        return str(e), None
    return None, account_data


def set_user_info(data: p_models.Account | p_models.Accountinfo, account_type: str = "Account") -> Any:
    try:
        if account_type == "Account":
            parsed_data = p_schemas.AccountGETALL.model_validate(data).model_dump_json()
        elif account_type == "Accountinfo":
            parsed_data = p_schemas.AccountinfoGET.model_validate(data).model_dump_json()
        else:
            return "Invalid account type"
        RedisSession.setex(f"{account_type}:{data.id}", Env.SCR_REFRESH_TOKEN_EXPIRE_MINUTES * 60, parsed_data)
    except Exception as e:
        return str(e)
