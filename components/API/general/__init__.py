from fastapi import APIRouter
from . import general, websocket

router_hub = APIRouter(prefix="/general")

router_hub.include_router(general.router)
router_hub.include_router(websocket.router)
