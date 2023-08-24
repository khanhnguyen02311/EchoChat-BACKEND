from fastapi import APIRouter
from . import signup, signin, logout, token

router_hub = APIRouter(prefix="/auth")

router_hub.include_router(signup.router)
router_hub.include_router(signin.router)
router_hub.include_router(token.router)
router_hub.include_router(logout.router)
