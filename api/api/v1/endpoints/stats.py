"""
Site-wide statistics endpoint with Redis caching.
"""

import json
import ssl
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlparse

import redis
from fastapi import APIRouter, Depends
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from api.api.deps import get_db
from api.api.lifecycle import openapi_lifecycle
from api.core.config import settings
from api.core.logging import get_logger
from api.models.tphoto import TPhoto
from api.models.trig import Trig
from api.models.user import TLog, User

logger = get_logger(__name__)
router = APIRouter()

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client singleton."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    if not settings.REDIS_URL:
        logger.debug("Redis not configured, caching disabled")
        return None

    try:
        redis_url = settings.REDIS_URL
        # Convert redis:// to rediss:// for serverless endpoints
        if "serverless" in redis_url and redis_url.startswith("redis://"):
            redis_url = redis_url.replace("redis://", "rediss://", 1)

        parsed = urlparse(redis_url)

        if parsed.scheme == "rediss":
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=10,
                retry_on_timeout=True,
                ssl=True,
                ssl_context=ssl_context,
            )
        else:
            _redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=10,
                retry_on_timeout=True,
            )

        logger.info(f"Redis client initialized for stats caching: {parsed.hostname}")
        return _redis_client
    except Exception as e:
        logger.warning(f"Failed to initialize Redis client: {e}")
        return None


@router.get("/site", openapi_extra=openapi_lifecycle("beta"))
def get_site_stats(db: Session = Depends(get_db)):
    """
    Get site-wide statistics.

    Returns:
    - total_trigs: Total number of trigpoints
    - total_users: Total number of registered users
    - total_logs: Total number of visit logs
    - total_photos: Total number of photos
    - recent_logs_7d: Number of logs in last 7 days
    - recent_users_30d: Number of users joined in last 30 days

    This endpoint is expensive to compute, so results are cached in Redis for 60 minutes.
    """
    cache_key = "site_stats:v1"
    cache_ttl = 3600  # 60 minutes

    # Try to get from cache
    redis_client = get_redis_client()
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data and isinstance(cached_data, str):
                logger.debug("Site stats served from cache")
                return json.loads(cached_data)
        except RedisError as e:
            logger.warning(f"Redis cache read failed: {e}")

    # Cache miss or Redis unavailable - compute stats
    logger.debug("Computing site stats from database")

    # Basic counts
    total_trigs = db.query(Trig).count()
    total_users = db.query(User).count()
    total_logs = db.query(TLog).count()
    total_photos = db.query(TPhoto).filter(TPhoto.deleted_ind != "Y").count()

    # Recent activity
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_logs_7d = db.query(TLog).filter(TLog.upd_timestamp >= seven_days_ago).count()

    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_users_30d = (
        db.query(User).filter(User.crt_date >= thirty_days_ago.date()).count()
    )

    result = {
        "total_trigs": total_trigs,
        "total_users": total_users,
        "total_logs": total_logs,
        "total_photos": total_photos,
        "recent_logs_7d": recent_logs_7d,
        "recent_users_30d": recent_users_30d,
    }

    # Store in cache
    if redis_client:
        try:
            redis_client.setex(cache_key, cache_ttl, json.dumps(result))
            logger.debug(f"Site stats cached for {cache_ttl}s")
        except RedisError as e:
            logger.warning(f"Redis cache write failed: {e}")

    return result
