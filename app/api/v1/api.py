"""
API v1 router that includes all endpoint routers.
"""
from app.api.v1.endpoints import auth, tlog, trig, user, users
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(user.router, prefix="/user", tags=["user"])
api_router.include_router(tlog.router, prefix="/tlog", tags=["tlog"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(trig.router, prefix="/trig", tags=["trig"])
