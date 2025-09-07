"""
Username analysis endpoints for checking duplicate sanitized usernames.
"""

from typing import Dict, List

from sqlalchemy.orm import Session

from app.crud.user import get_all_usernames
from app.db.database import get_db
from app.utils.username_sanitizer import find_duplicate_sanitized_usernames
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.get("/username-duplicates")
def get_username_duplicates(db: Session = Depends(get_db)) -> Dict[str, List[str]]:
    """
    Get all usernames from the legacy database and identify duplicates after sanitization.

    This endpoint:
    1. Retrieves all usernames from the legacy database
    2. Sanitizes each username according to Auth0 rules
    3. Identifies which original usernames map to the same sanitized username
    4. Returns a JSON object showing all duplicates

    Returns:
        Dictionary mapping sanitized usernames to lists of original usernames that map to them.
        Only includes entries where multiple original usernames map to the same sanitized username.

    Example response:
        {
            "user_name": ["user name", "user-name", "user_name"],
            "user@example.com": ["user@example.com", "user@test.com"]
        }
    """
    try:
        # Get all usernames from the legacy database
        usernames = get_all_usernames(db)

        if not usernames:
            return {}

        # Find duplicates after sanitization
        duplicates = find_duplicate_sanitized_usernames(usernames)

        return duplicates

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing username duplicates: {str(e)}",
        )
