from fastapi import APIRouter
from . import signup

router_hub = APIRouter(prefix="/auth")

router_hub.include_router(signup.router)
