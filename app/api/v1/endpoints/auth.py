"""
Authentication endpoints.
"""
from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import authenticate_user_flexible
from app.db.database import get_db
from app.schemas.user import Token
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Login endpoint to get JWT access token.

    Accepts either email address or username in the 'username' field.
    Auto-detects the type and authenticates accordingly.

    Examples:
    - username: "john@example.com" (email)
    - username: "johndoe" (username)
    """
    user = authenticate_user_flexible(
        db, identifier=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
