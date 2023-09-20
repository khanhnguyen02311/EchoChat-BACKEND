from fastapi import APIRouter
from . import authentication, user, chat

router_super_hub = APIRouter()

router_super_hub.include_router(authentication.router_hub)
router_super_hub.include_router(user.router_hub)
router_super_hub.include_router(chat.router_hub)
