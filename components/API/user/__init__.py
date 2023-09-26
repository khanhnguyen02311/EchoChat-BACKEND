from fastapi import APIRouter
from . import me

router_hub = APIRouter(prefix="/user")

router_hub.include_router(me.router)
