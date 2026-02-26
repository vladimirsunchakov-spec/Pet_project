from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from starlette.middleware.cors import CORSMiddleware
from src.healthcheck.router import router as healthcheck_router
from src.routers.authors import router as authors_router
from src.routers.books import router as books_router
from src.routers.countries import router as countries_router
from src.routers.cities import router as cities_router
from src.routers.users import router as users_router
from src.routers.passports import router as passports_router

def get_app() -> FastAPI:

    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    app = FastAPI(
        docs_url='/docs',
        openapi_url='/openapi.json',
        default_response_class=UJSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(healthcheck_router)
    app.include_router(authors_router)
    app.include_router(books_router)
    app.include_router(countries_router)
    app.include_router(cities_router)
    app.include_router(users_router)
    app.include_router(passports_router)


    return app