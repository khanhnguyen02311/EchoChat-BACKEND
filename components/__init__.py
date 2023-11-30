from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from configurations import conf
from components.API import super_hub
# from components.utilities.tracers import setting_otlp
from prometheus_fastapi_instrumentator import Instrumentator

tags_metadata = [
    {
        "name": "authentication",
        "description": "Operations with authentication methods & user validation",
    },
    {
        "name": "user",
        "description": "Operations with user information",
    },
    {
        "name": "chat",
        "description": "Operations with group, participants and messages",
    },
]


def serve_api(debug: bool, stage: str):
    server = FastAPI(debug=debug, openapi_tags=tags_metadata, redoc_url=None)
    server.add_middleware(
        CORSMiddleware,
        allow_origins=[conf.Env.APP_FRONTEND_URL],  # your frontend port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[""]
    )
    server.include_router(super_hub)
    if stage in ['staging', 'prod']:
        Instrumentator().instrument(server).expose(server)
        # setting_otlp(app, log_correlation=False)
    return server
