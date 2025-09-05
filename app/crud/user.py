"""
CRUD operations for users with Unix crypt authentication.
"""

import crypt
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth0_service import auth0_service

logger = logging.getLogger(__name__)


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.

    Args:
        db: Database session
        email: Email address

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_name(db: Session, name: str) -> Optional[User]:
    """
    Get a user by username.

    Args:
        db: Database session
        name: Username

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.name == name).first()


def verify_password(plain_password: str, cryptpw: str) -> bool:
    """
    Verify a password against Unix crypt hash.

    This matches the PHP logic: crypt($_POST['loginpw'], $cryptpw) == $cryptpw

    Args:
        plain_password: Plain text password
        cryptpw: Unix crypt hash from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        return crypt.crypt(plain_password, cryptpw) == cryptpw
    except OSError:
        # crypt() can raise OSError on some systems
        return False


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password (legacy function for compatibility).

    Args:
        db: Database session
        email: Email address
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, str(user.cryptpw)):
        return None
    return user


def authenticate_user_flexible(
    db: Session, identifier: str, password: str
) -> Optional[User]:
    """
    Authenticate a user with either email or username.

    Auto-detects the identifier type:
    - Contains '@' -> treated as email
    - No '@' -> treated as username
    - Falls back to alternate method if first fails

    After successful authentication, syncs the user to Auth0 if enabled.

    Args:
        db: Database session
        identifier: Email address or username
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    user = None

    # Primary detection: email vs username
    if "@" in identifier:
        # Looks like email - try email first, then username fallback
        user = get_user_by_email(db, identifier)
        if not user:
            # Fallback: maybe it's a username that contains @
            user = get_user_by_name(db, identifier)
    else:
        # Looks like username - try username first, then email fallback
        user = get_user_by_name(db, identifier)
        if not user:
            # Fallback: maybe it's an email without obvious @ structure
            user = get_user_by_email(db, identifier)

    # Verify password if user found
    if not user:
        return None
    if not verify_password(password, str(user.cryptpw)):
        return None

    # Sync user to Auth0 after successful authentication
    try:
        auth0_service.sync_user_to_auth0(
            username=str(user.name),
            email=str(user.email) if user.email else None,
            name=str(user.name),
            password=password,  # Use the plaintext password from the login request
            user_id=int(user.id),
        )
    except Exception as e:
        # Log the error but don't fail authentication
        logger.error(
            "Auth0 sync failed during authentication",
            extra={
                "user_id": user.id,
                "username": user.name,
                "email": user.email,
                "error": str(e),
            },
        )

    return user


def is_admin(user: User) -> bool:
    """
    Check if user has admin privileges.

    Args:
        user: User object

    Returns:
        True if user is admin, False otherwise
    """
    return str(user.admin_ind) == "Y"


def is_public_profile(user: User) -> bool:
    """
    Check if user has a public profile.

    Args:
        user: User object

    Returns:
        True if profile is public, False otherwise
    """
    return str(user.public_ind) == "Y"


def search_users_by_name(
    db: Session, name_pattern: str, skip: int = 0, limit: int = 100
) -> list[User]:
    """
    Search users by name pattern.

    Args:
        db: Database session
        name_pattern: Name pattern to search for (case-insensitive)
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of User objects
    """
    return (
        db.query(User)
        .filter(User.name.ilike(f"%{name_pattern}%"))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_users_count(db: Session) -> int:
    """
    Get total number of users.

    Args:
        db: Database session

    Returns:
        Total count of users
    """
    return db.query(User).count()
