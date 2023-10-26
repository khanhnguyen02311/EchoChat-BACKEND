from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from configurations import conf
from components.API import super_hub


def create_app(debug: bool):
    app = FastAPI(debug=debug)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[conf.Env.APP_FRONTEND_URL],  # your frontend port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[""]
    )
    app.include_router(super_hub)

    return app
