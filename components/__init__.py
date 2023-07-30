from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import components.apis

origins = ["http://localhost:5173"]  # your frontend location


def create_app(debug: bool):
    app = FastAPI(debug=debug)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[""]
    )

    app.include_router(apis.router)

    return app
