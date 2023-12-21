from fastapi import APIRouter
from configurations.conf import Env
from components.data import ScyllaSession
# Endpoint-level hubs
from .system import system
from .authentication import signup, signin, signout, token
from .user import me, search
from .chat import group, message

system_hub = APIRouter(prefix="/system", tags=["system"])
system_hub.include_router(system.router)

authentication_hub = APIRouter(prefix="/auth", tags=["authentication"])
authentication_hub.include_router(signup.router)
authentication_hub.include_router(signin.router)
authentication_hub.include_router(signout.router)
authentication_hub.include_router(token.router)

chat_hub = APIRouter(prefix="/chat")
chat_hub.include_router(group.router, tags=["group"])
chat_hub.include_router(message.router, tags=["message"])

user_hub = APIRouter(prefix="/user", tags=["user"])
user_hub.include_router(me.router)
user_hub.include_router(search.router)

# ----------------------------------------
# Now unsupported, use EchoChat-WS instead
# from .ws import ws
# ws_hub = APIRouter(prefix="/ws")
# ws_hub.include_router(ws.router)
# ----------------------------------------

# Super hub
super_hub = APIRouter()
super_hub.include_router(authentication_hub)
super_hub.include_router(chat_hub)
super_hub.include_router(user_hub)
super_hub.include_router(system_hub)


@super_hub.get("/")
def hello_echochat():
    return "EchoChat!"
