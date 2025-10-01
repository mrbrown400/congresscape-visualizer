"""FastAPI application instance."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Place for startup/shutdown hooks (e.g., initialize schedulers)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name, debug=settings.debug, lifespan=lifespan)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
