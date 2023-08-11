from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from components.API import general, authentication
from components.storages import postgres_models
from configurations import conf


def create_app(debug: bool):
    app = FastAPI(debug=debug)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[conf.Env.APP_FRONTEND_URL],  # your frontend port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[""]
    )
    app.include_router(general.router)
    app.include_router(authentication.router_hub)

    return app
