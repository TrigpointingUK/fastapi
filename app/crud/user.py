"""
CRUD operations for users with Unix crypt authentication.
"""

import crypt
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.user import TLog, User
from app.services.auth0_service import auth0_service
from app.utils.username_sanitizer import sanitize_username_for_auth0

logger = get_logger(__name__)


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
    logger.info(
        "authenticate_user_flexible called",
        extra={
            "identifier": identifier,
            "password_provided": bool(password),
            "password_length": len(password) if password else 0,
        },
    )
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
        logger.info(
            "User not found in database",
            extra={"identifier": identifier},
        )
        return None
    if not verify_password(password, str(user.cryptpw)):
        logger.info(
            "Password verification failed",
            extra={"identifier": identifier, "user_id": user.id},
        )
        return None

    logger.info(
        "User authentication successful",
        extra={
            "identifier": identifier,
            "user_id": user.id,
            "username": user.name,
            "email": user.email,
        },
    )

    # Sync user to Auth0 after successful authentication
    try:
        logger.info(
            "Starting Auth0 sync for user",
            extra={
                "user_id": user.id,
                "username": user.name,
                "email": user.email,
                "auth0_enabled": auth0_service.enabled,
            },
        )
        auth0_service.sync_user_to_auth0(
            username=str(user.name),
            email=str(user.email) if user.email else None,
            name=str(user.name),
            password=password,  # Use the plaintext password from the login request
            user_id=int(user.id),
            firstname=str(user.firstname) if user.firstname else None,
            surname=str(user.surname) if user.surname else None,
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


def is_cacher(user: User) -> bool:
    """
    Check if user is a geocacher.

    Args:
        user: User object

    Returns:
        True if user is a geocacher, False otherwise
    """
    return str(user.cacher_ind) == "Y"


def is_trigger(user: User) -> bool:
    """
    Check if user is a trigger.

    Args:
        user: User object

    Returns:
        True if user is a trigger, False otherwise
    """
    return str(user.trigger_ind) == "Y"


def is_email_validated(user: User) -> bool:
    """
    Check if user's email is validated.

    Args:
        user: User object

    Returns:
        True if email is validated, False otherwise
    """
    return str(user.email_valid) == "Y"


def has_gc_auth(user: User) -> bool:
    """
    Check if user has Geocaching.com authentication.

    Args:
        user: User object

    Returns:
        True if user has GC auth, False otherwise
    """
    return str(user.gc_auth_ind) == "Y"


def has_gc_premium(user: User) -> bool:
    """
    Check if user has Geocaching.com premium status.

    Args:
        user: User object

    Returns:
        True if user has GC premium, False otherwise
    """
    return str(user.gc_premium_ind) == "Y"


def get_all_usernames(db: Session) -> List[str]:
    """
    Get all usernames from the legacy database.

    Args:
        db: Database session

    Returns:
        List of all usernames in the database
    """
    users = db.query(User).all()
    return [str(user.name) for user in users if user.name]


def get_user_log_stats(db: Session, user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Get log statistics for a list of user IDs.
    Returns a dictionary mapping user_id to log count and latest log timestamp.

    Args:
        db: Database session
        user_ids: List of user IDs to get log stats for

    Returns:
        Dictionary mapping user_id to log statistics
    """
    if not user_ids:
        return {}

    # Get log count and latest log timestamp for each user
    log_stats = (
        db.query(
            TLog.user_id,
            func.count(TLog.id).label("log_count"),
            func.max(func.concat(TLog.date, " ", TLog.time)).label(
                "latest_log_timestamp"
            ),
        )
        .filter(TLog.user_id.in_(user_ids))
        .group_by(TLog.user_id)
        .all()
    )

    # Convert to dictionary
    result = {}
    for user_id, log_count, latest_log_timestamp in log_stats:
        result[user_id] = {
            "log_count": log_count,
            "latest_log_timestamp": latest_log_timestamp,
        }

    return result


def get_all_emails(db: Session) -> List[str]:
    """
    Get all email addresses from the legacy database.

    Args:
        db: Database session

    Returns:
        List of all email addresses in the database
    """
    users = db.query(User).all()
    return [str(user.email) for user in users if user.email]


def find_duplicate_emails(emails: List[str]) -> Dict[str, List[str]]:
    """
    Find duplicate email addresses (case-insensitive).

    Args:
        emails: List of email addresses

    Returns:
        Dictionary mapping email addresses to lists of original email addresses
        that are duplicates (case-insensitive). Only includes entries where
        multiple email addresses map to the same normalized email.
    """
    email_to_originals: Dict[str, List[str]] = {}

    for email in emails:
        if not email:
            continue
        # Normalize email to lowercase for comparison
        normalized = email.lower().strip()
        if normalized not in email_to_originals:
            email_to_originals[normalized] = []
        email_to_originals[normalized].append(email)

    # Return only duplicates
    duplicates = {
        normalized: originals
        for normalized, originals in email_to_originals.items()
        if len(originals) > 1
    }
    return duplicates


def get_users_by_email(db: Session, email: str) -> List[User]:
    """
    Get all users with a specific email address (case-insensitive).

    Args:
        db: Database session
        email: Email address to search for

    Returns:
        List of User objects with the specified email address
    """
    return db.query(User).filter(func.lower(User.email) == email.lower()).all()


def get_user_by_auth0_id(db: Session, auth0_user_id: str) -> Optional[User]:
    """
    Get a user by Auth0 user ID.

    Args:
        db: Database session
        auth0_user_id: Auth0 user ID

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.auth0_user_id == auth0_user_id).first()


def update_user_auth0_id(db: Session, user_id: int, auth0_user_id: str) -> bool:
    """
    Update user's Auth0 user ID.

    Args:
        db: Database session
        user_id: Database user ID
        auth0_user_id: Auth0 user ID

    Returns:
        True if successful, False otherwise
    """
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return False  # pragma: no cover

    user.auth0_user_id = auth0_user_id  # type: ignore
    db.commit()

    return True


def update_user_auth0_mapping(
    db: Session, user_id: int, auth0_user_id: str, auth0_username: Optional[str]
) -> bool:
    """
    Update user's Auth0 mapping: both user ID and username.

    Also performs a sanity check comparing the Auth0 username with the
    sanitized version of the legacy username. If they differ, log an error
    but continue processing.

    Args:
        db: Database session
        user_id: Legacy database user ID
        auth0_user_id: Auth0 user ID (e.g. "auth0|abc123")
        auth0_username: Username value returned by Auth0 (sanitized by Auth0)

    Returns:
        True if update succeeded (at least the ID), False otherwise.
    """
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return False

    # Sanity check: compare Auth0 username with sanitized legacy username
    try:
        if auth0_username:
            sanitized_legacy = sanitize_username_for_auth0(str(user.name))
            if str(auth0_username) != sanitized_legacy:
                logger.error(
                    "Auth0 username mismatch after sanitization",
                    extra={
                        "user_id": user_id,
                        "legacy_username": str(user.name),
                        "sanitized_legacy_username": sanitized_legacy,
                        "auth0_username": str(auth0_username),
                        "auth0_user_id": str(auth0_user_id),
                    },
                )
    except Exception as e:  # Defensive: do not block update on check failure
        logger.error(  # pragma: no cover
            "Auth0 username sanity check failed",
            extra={"user_id": user_id, "error": str(e)},
        )

    # Try to set both fields
    try:
        user.auth0_user_id = auth0_user_id  # type: ignore
        if auth0_username is not None:
            user.auth0_username = str(auth0_username)  # type: ignore
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.warning(  # pragma: no cover
            "Auth0 mapping update failed when setting username; retrying with ID only",
            extra={"user_id": user_id, "error": str(e)},
        )

        # Fallback: update only the ID to avoid losing the linkage
        try:
            user.auth0_user_id = auth0_user_id  # type: ignore  # pragma: no cover
            db.commit()  # pragma: no cover
            return True  # pragma: no cover
        except Exception as e2:
            db.rollback()
            logger.error(  # pragma: no cover
                "Auth0 mapping update failed",
                extra={"user_id": user_id, "error": str(e2)},
            )
            return False  # pragma: no cover


def get_user_auth0_id(db: Session, user_id: int) -> Optional[str]:
    """
    Get Auth0 user ID for a database user.

    Args:
        db: Database session
        user_id: Database user ID

    Returns:
        Auth0 user ID or None if not found
    """
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None
    return user.auth0_user_id  # type: ignore
