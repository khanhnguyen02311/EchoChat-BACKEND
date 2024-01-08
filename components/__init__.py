from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from configurations import conf
from components.API import super_hub
# from components.utilities.tracers import setting_otlp
from prometheus_fastapi_instrumentator import Instrumentator
from components.services.proto import EchoChat_pb2_grpc, services_grpc
from components.services.rabbitmq import services_rabbitmq
from concurrent import futures
import grpc

tags_metadata = [
    {
        "name": "system",
        "description": "Operations with application system",
    },
    {
        "name": "authentication",
        "description": "Operations with authentication methods & user validation",
    },
    {
        "name": "user",
        "description": "Operations with user information",
    },
    {
        "name": "group",
        "description": "Operations with group and participants",
    },
    {
        "name": "message",
        "description": "Operations with chat messages",
    },
    {
        "name": "notification",
        "description": "Operations with message & other types of notifications",
    },
    {
        "name": "ws",
        "description": "Operations with websocket",
    },
]


def serve_api(debug: bool, stage: str):
    cors_origins = conf.Env.APP_FRONTEND_URLS.split(",")
    server = FastAPI(debug=debug, openapi_tags=tags_metadata, redoc_url=None)
    server.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,  # your frontend urls
        allow_credentials=True,
        allow_methods=["GET", "PUT", "POST", "DELETE", "PATCH"],  # OPTIONS method is handled by NGINX
        allow_headers=["*"]
    )
    server.include_router(super_hub)
    if stage in ['staging', 'prod']:
        Instrumentator().instrument(server).expose(server)
        # setting_otlp(app, log_correlation=False)
    return server


def serve_grpc(debug: bool, stage: str):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1 if stage == "dev" else 2))
    EchoChat_pb2_grpc.add_EchoChatBEServicer_to_server(services_grpc.BEServicerGRPC(), server)
    return server
