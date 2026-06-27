from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from starlette.middleware.cors import CORSMiddleware
from src.core.logger import setup_logging
from src.core.redis import redis_client
from src.middleware.request_id import RequestIdMiddleware
from src.healthcheck.router import router as healthcheck_router
from src.routers.authors_books import router as authors_books_router
from src.routers.countries_cities import router as countries_cities_router
from src.routers.users_passports import router as users_passports_router
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.initialize()
    logger.info("Redis connection")

    yield

    await redis_client.close()
    logger.info("Redis connection closed")

def register_routes(app: FastAPI) -> None:
    app.include_router(healthcheck_router)
    app.include_router(authors_books_router)
    app.include_router(countries_cities_router)
    app.include_router(users_passports_router)

def get_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        docs_url='/docs',
        openapi_url='/openapi.json',
        default_response_class=UJSONResponse,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.add_middleware(RequestIdMiddleware)

    register_routes(app)
    return app