"""
API v1 router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    debug,
    photo,
    tlog,
    trig,
    user,
    username_analysis,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/legacy", tags=["legacy"])
api_router.include_router(user.router, prefix="/users", tags=["user"])
api_router.include_router(tlog.router, prefix="/tlogs", tags=["tlog"])
# removed legacy users subrouter
api_router.include_router(trig.router, prefix="/trigs", tags=["trig"])
api_router.include_router(photo.router, prefix="/photos", tags=["photo"])
api_router.include_router(username_analysis.router, prefix="/legacy", tags=["legacy"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])
