"""
Username analysis endpoints for checking duplicate sanitized usernames.
"""

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.crud.user import get_all_usernames, get_user_by_name, get_user_log_stats
from app.db.database import get_db
from app.utils.username_sanitizer import find_duplicate_sanitized_usernames
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.get("/username-duplicates")
def get_username_duplicates(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get all usernames from the legacy database and identify duplicates after sanitization.

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
                        "log_count": 45,
                        "latest_log_timestamp": "2023-12-15 14:30:00"
                    },
                    {
                        "username": "user-name",
                        "user_id": 456,
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

            for username in original_usernames:
                user = get_user_by_name(db, username)
                if user:
                    user_ids.append(user.id)
                    username_to_user_id[username] = user.id

            # Get log statistics for all users
            log_stats = get_user_log_stats(db, user_ids)

            # Build user information with log stats
            users_with_logs = []
            for username in original_usernames:
                user_id = username_to_user_id.get(username)
                if user_id:
                    user_log_info = log_stats.get(
                        user_id, {"log_count": 0, "latest_log_timestamp": None}
                    )
                    users_with_logs.append(
                        {
                            "username": username,
                            "user_id": user_id,
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
