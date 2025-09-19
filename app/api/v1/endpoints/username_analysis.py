"""
Username analysis endpoints for checking duplicate sanitized usernames.
"""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.crud.user import (
    find_duplicate_emails,
    get_all_emails,
    get_all_usernames,
    get_user_by_name,
    get_user_log_stats,
    get_users_by_email,
)
from app.models.user import User
from app.utils.username_sanitizer import find_duplicate_sanitized_usernames
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.get("/username-duplicates")
def get_username_duplicates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Get all usernames from the legacy database and identify duplicates after sanitization.

    **Requires admin privileges (admin_ind='Y')**

    This endpoint:
    1. Retrieves all usernames from the legacy database
    2. Sanitizes each username according to Auth0 rules
    3. Identifies which original usernames map to the same sanitized username
    4. For each duplicate user, includes log count and latest log timestamp
    5. Returns a JSON object showing all duplicates with log information

    Returns:
        Dictionary mapping sanitized usernames to user information including:
        - original_usernames: List of original usernames that map to this sanitized username
        - users: List of user objects with log statistics for each duplicate user

    Example response:
        {
            "user_name": {
                "original_usernames": ["user name", "user-name", "user_name"],
                "users": [
                    {
                        "username": "user name",
                        "user_id": 123,
                        "email": "user1@example.com",
                        "log_count": 45,
                        "latest_log_timestamp": "2023-12-15 14:30:00"
                    },
                    {
                        "username": "user-name",
                        "user_id": 456,
                        "email": "user2@example.com",
                        "log_count": 23,
                        "latest_log_timestamp": "2023-11-20 09:15:00"
                    }
                ]
            }
        }
    """
    try:
        # Get all usernames from the legacy database
        usernames = get_all_usernames(db)

        if not usernames:
            return {}

        # Find duplicates after sanitization
        duplicates = find_duplicate_sanitized_usernames(usernames)

        # Enhance with log information
        enhanced_duplicates = {}

        for sanitized_username, original_usernames in duplicates.items():
            # Get user IDs for all original usernames
            user_ids = []
            username_to_user_id = {}
            username_to_user = {}

            for username in original_usernames:
                user = get_user_by_name(db, username)
                if user and user.id is not None:
                    user_id = int(user.id)
                    user_ids.append(user_id)
                    username_to_user_id[username] = user_id
                    # Store user object for later use
                    username_to_user[username] = user

            # Get log statistics for all users
            log_stats = get_user_log_stats(db, user_ids)

            # Build user information with log stats
            users_with_logs = []
            for username in original_usernames:
                current_user_id: int | None = username_to_user_id.get(username)
                if current_user_id is not None:
                    user = username_to_user.get(username)
                    user_log_info = log_stats.get(
                        current_user_id, {"log_count": 0, "latest_log_timestamp": None}
                    )
                    users_with_logs.append(
                        {
                            "username": username,
                            "user_id": current_user_id,
                            "email": str(user.email) if user and user.email else "",
                            "log_count": user_log_info["log_count"],
                            "latest_log_timestamp": user_log_info[
                                "latest_log_timestamp"
                            ],
                        }
                    )

            enhanced_duplicates[sanitized_username] = {
                "original_usernames": original_usernames,
                "users": users_with_logs,
            }

        return enhanced_duplicates

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing username duplicates: {str(e)}",
        )


@router.get("/email-duplicates")
def get_email_duplicates(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_admin_user),
) -> Dict[str, Any]:
    """
    Get all email addresses from the legacy database and identify duplicates.

    **Requires admin privileges (admin_ind='Y')**

    This endpoint:
    1. Retrieves all email addresses from the legacy database
    2. Identifies which email addresses are used by multiple users (case-insensitive)
    3. For each duplicate email, includes log count and latest log timestamp for each user
    4. Returns a JSON object showing all duplicate emails with log information
    5. Supports pagination to prevent timeouts with large datasets

    Args:
        limit: Maximum number of duplicate email addresses to process (default: 50)
        offset: Number of duplicate email addresses to skip (default: 0)

    Returns:
        Dictionary mapping normalized email addresses to user information including:
        - original_emails: List of original email addresses that are duplicates
        - users: List of user objects with log statistics for each user with this email
        - pagination: Information about current page and total counts

    Example response:
        {
            "user@example.com": {
                "original_emails": ["user@example.com", "User@Example.com"],
                "users": [
                    {
                        "username": "user1",
                        "user_id": 123,
                        "email": "user@example.com",
                        "log_count": 45,
                        "latest_log_timestamp": "2023-12-15 14:30:00"
                    },
                    {
                        "username": "user2",
                        "user_id": 456,
                        "email": "User@Example.com",
                        "log_count": 23,
                        "latest_log_timestamp": "2023-11-20 09:15:00"
                    }
                ]
            },
            "pagination": {
                "limit": 50,
                "offset": 0,
                "total_duplicates": 150,
                "has_more": true
            }
        }
    """
    # Validate pagination parameters
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be greater than 0",
        )
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be 0 or greater",
        )
    if limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Limit cannot exceed 1000"
        )

    try:
        # Get all email addresses from the legacy database
        emails = get_all_emails(db)

        if not emails:
            return {
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total_duplicates": 0,
                    "has_more": False,
                }
            }

        # Find duplicates after normalization (case-insensitive)
        duplicates = find_duplicate_emails(emails)

        # Apply pagination to duplicate emails
        total_duplicates = len(duplicates)
        duplicate_items = list(duplicates.items())
        paginated_duplicates = duplicate_items[offset : offset + limit]

        # Enhance with log information
        enhanced_duplicates = {}

        for normalized_email, original_emails in paginated_duplicates:
            # Get all users with this email address
            users_with_email = get_users_by_email(db, normalized_email)

            if not users_with_email:
                continue

            # Get user IDs for log statistics
            user_ids = [
                int(user.id) for user in users_with_email if user.id is not None
            ]

            # Get log statistics for all users
            log_stats = get_user_log_stats(db, user_ids)

            # Build user information with log stats
            users_with_logs = []
            for user in users_with_email:
                if user.id is not None:
                    user_id = int(user.id)
                    user_log_info = log_stats.get(
                        user_id, {"log_count": 0, "latest_log_timestamp": None}
                    )
                    users_with_logs.append(
                        {
                            "username": str(user.name) if user.name else "",
                            "user_id": user_id,
                            "email": str(user.email) if user.email else "",
                            "log_count": user_log_info["log_count"],
                            "latest_log_timestamp": user_log_info[
                                "latest_log_timestamp"
                            ],
                        }
                    )

            enhanced_duplicates[normalized_email] = {
                "original_emails": original_emails,
                "users": users_with_logs,
            }

        # Add pagination information
        enhanced_duplicates["pagination"] = {
            "limit": limit,
            "offset": offset,
            "total_duplicates": total_duplicates,
            "has_more": offset + limit < total_duplicates,
        }

        return enhanced_duplicates

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing email duplicates: {str(e)}",
        )
