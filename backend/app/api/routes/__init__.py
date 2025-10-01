"""API router registration."""
from fastapi import APIRouter

from . import feeds, ingest, system

api_router = APIRouter()
api_router.include_router(system.router, tags=["system"])
api_router.include_router(feeds.router, prefix="/feed", tags=["feed"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
