from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from components.data import PostgresSession
from components.data.schemas import postgres_schemas as p_schemas
from components.data.models import postgres_models as p_models

router = APIRouter()


@router.get("/search")
async def search_user(name: str, identifier: int | None = None):
    with PostgresSession.begin() as session:
        try:
            if len(name) < 3:
                raise Exception("Search phrase too short")
            accountinfo_query = select(p_models.Accountinfo).where(p_models.Accountinfo.name.contains(name))
            if identifier is not None:
                accountinfo_query = accountinfo_query.where(p_models.Accountinfo.identifier == identifier)
            accountinfo_list = session.scalars(accountinfo_query)
            return p_schemas.ListAccountinfoGET.model_validate(accountinfo_list).model_dump()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=str(e))
