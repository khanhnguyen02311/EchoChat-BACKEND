from fastapi import APIRouter, Depends
from components.functions.security import handle_deactivate_token

router = APIRouter()


@router.post("/logout", dependencies=[Depends(handle_deactivate_token)])
async def logout():
    return "Done"
