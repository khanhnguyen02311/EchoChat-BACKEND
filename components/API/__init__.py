from fastapi import APIRouter
from configurations.conf import Env
from components.storages import ScyllaSession
# Endpoint-level hubs
from .authentication import signup, signin, logout, token
from .user import me, search
from .chat import group
from .ws import ws

authentication_hub = APIRouter(prefix="/auth")
authentication_hub.include_router(signup.router)
authentication_hub.include_router(signin.router)
authentication_hub.include_router(token.router)
authentication_hub.include_router(logout.router)

chat_hub = APIRouter(prefix="/chat")
chat_hub.include_router(group.router)

user_hub = APIRouter(prefix="/user")
user_hub.include_router(me.router)
user_hub.include_router(search.router)

ws_hub = APIRouter(prefix="/ws")
ws_hub.include_router(ws.router)

# Super hub
super_hub = APIRouter()
super_hub.include_router(authentication_hub)
super_hub.include_router(chat_hub)
super_hub.include_router(user_hub)


@super_hub.get("/")
def default():
    # with PostgresSession() as session:
    #     postgres_mains = session.execute(text("SELECT client_addr, state FROM pg_stat_replication;")).scalars()
    #     session.close()

    scylla_mains = ScyllaSession.execute(
        "SELECT rack, schema_version, host_id, rpc_address, data_center FROM system.local").all()
    scylla_peers = ScyllaSession.execute(
        "SELECT rack, schema_version, host_id, rpc_address, data_center FROM system.peers").all()

    return {
        "app": "EchoChat",
        "stage": Env.APP_STAGE,
        "debug": Env.APP_DEBUG,
        "scylla": {
            "main_nodes": scylla_mains,
            "peer_nodes": scylla_peers,
        },
    }
