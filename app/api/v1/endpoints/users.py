"""
User endpoints with JWT protection.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud.user import get_user_by_id, is_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserEmail

router = APIRouter()


@router.get("/email/{user_id}", response_model=UserEmail)
def get_user_email(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    JWT-protected endpoint to get user email address.
    
    Only allows access if:
    - The authenticated user is requesting their own email, OR
    - The authenticated user has admin privileges (admin_ind='Y')
    
    Args:
        user_id: The ID of the user whose email is being requested
        
    Returns:
        UserEmail: Object containing user_id and email
        
    Raises:
        HTTPException: 403 if user doesn't have permission
        HTTPException: 404 if requested user doesn't exist
    """
    # Check if user is requesting their own email or is an admin
    if current_user.user_id != user_id and not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user's email"
        )
    
    # Get the requested user
    target_user = get_user_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserEmail(user_id=target_user.user_id, email=target_user.email)
