from fastapi import APIRouter

# Endpoint-level hubs
from .authentication import signup, signin, logout, token
from .user import me, search
from .chat import group, message

authentication_hub = APIRouter(prefix="/auth")
authentication_hub.include_router(signup.router)
authentication_hub.include_router(signin.router)
authentication_hub.include_router(token.router)
authentication_hub.include_router(logout.router)

chat_hub = APIRouter(prefix="/chat")
chat_hub.include_router(group.router)
chat_hub.include_router(message.router)

user_hub = APIRouter(prefix="/user")
user_hub.include_router(me.router)
user_hub.include_router(search.router)

# Super hub
super_hub = APIRouter()
super_hub.include_router(authentication_hub)
super_hub.include_router(chat_hub)
super_hub.include_router(user_hub)
