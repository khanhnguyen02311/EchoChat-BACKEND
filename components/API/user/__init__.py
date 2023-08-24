from fastapi import APIRouter
from . import user

router_hub = APIRouter(prefix="/user")

router_hub.include_router(user.router)
