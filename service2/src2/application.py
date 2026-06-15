from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from starlette.middleware.cors import CORSMiddleware
from service2.src2.core.logger import setup_logging
from service2.src2.middleware.request_id import RequestIdMiddleware
from service2.src2.routers import bio
from service2.src2.db import engine

@asynccontextmanager
async def life_span(app: FastAPI):
    setup_logging()
    print("Logging configured")

    yield

    await engine.dispose()
    print("Database connections closed")

def register_routes(app: FastAPI) -> None:
    app.include_router(bio.router)

def get_app() -> FastAPI:

    app = FastAPI(
        title="Bio Service",
        description="Сервис для хранения дополнительной информации об авторах",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        default_response_class=UJSONResponse,
        lifespan=life_span,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIdMiddleware)

    register_routes(app)
    return app


