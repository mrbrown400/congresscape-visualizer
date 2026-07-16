"""API router registration."""
from fastapi import APIRouter

from . import feeds, geography, ingest, members, notifications, summary, system

api_router = APIRouter()
api_router.include_router(system.router, tags=["system"])
api_router.include_router(feeds.router, prefix="/feed", tags=["feed"])
api_router.include_router(geography.router, prefix="/geography", tags=["geography"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(members.router, prefix="/members", tags=["members"])
api_router.include_router(summary.router, prefix="/summary", tags=["summary"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
