"""
API v1 router that includes all endpoint routers.
"""

from app.api.v1.endpoints import (
    debug,
    legacy,
    logs,
    photos,
    trigs,
    users,
)
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(trigs.router, prefix="/trigs", tags=["trig"])
api_router.include_router(users.router, prefix="/users", tags=["user"])
api_router.include_router(logs.router, prefix="/logs", tags=["log"])
api_router.include_router(photos.router, prefix="/photos", tags=["photo"])
api_router.include_router(legacy.router, prefix="/legacy", tags=["legacy"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
