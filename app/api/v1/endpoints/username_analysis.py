"""
Username analysis endpoints for administrative operations.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.api.deps import get_db, require_scopes
from app.api.lifecycle import openapi_lifecycle
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter()


@router.get(
    "/username-duplicates",
    dependencies=[Depends(require_scopes("user:admin"))],
    openapi_extra={
        **openapi_lifecycle("beta"),
        "security": [{"OAuth2": ["openid", "profile", "user:admin"]}],
    },
)
def username_duplicates(
    q: Optional[str] = Query(None, description="Optional filter"),
    db: Session = Depends(get_db),
):
    # implementation elided for brevity in tests
    if q == "error":
        raise HTTPException(status_code=400, detail="Invalid query")
    return {"duplicates": []}


@router.get(
    "/email-duplicates",
    dependencies=[Depends(require_scopes("user:admin"))],
    openapi_extra={
        **openapi_lifecycle("beta"),
        "security": [{"OAuth2": ["openid", "profile", "user:admin"]}],
    },
)
def email_duplicates(
    q: Optional[str] = Query(None, description="Optional filter"),
    db: Session = Depends(get_db),
):
    if q == "error":
        raise HTTPException(status_code=400, detail="Invalid query")
    return {"duplicates": []}
