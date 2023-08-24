from fastapi import APIRouter
from . import group, message

router_hub = APIRouter(prefix="/chat")

router_hub.include_router(group.router)
router_hub.include_router(message.router)
