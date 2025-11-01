"""
Tests for user creation CRUD function.
"""

import pytest
from sqlalchemy.orm import Session

from api.crud.user import (
    create_user,
    get_user_by_auth0_id,
    get_user_by_email,
    get_user_by_name,
)


def test_create_user_success(db: Session):
    """Test successful user creation."""
    username = "testuser"
    email = "test@example.com"
    auth0_user_id = "auth0|12345"

    user = create_user(
        db=db,
        username=username,
        email=email,
        auth0_user_id=auth0_user_id,
    )

    assert user.id is not None
    assert user.name == username
    assert user.email == email
    assert user.auth0_user_id == auth0_user_id
    assert user.firstname == ""
    assert user.surname == ""
    assert user.email_valid == "Y"
    assert user.public_ind == "N"
    assert user.cryptpw != ""  # Should be set to random string
    assert len(user.cryptpw) > 20  # Random token should be reasonably long
    assert user.crt_date is not None
    assert user.crt_time is not None


def test_create_user_cryptpw_is_random(db: Session):
    """Test that cryptpw is set to a random string, not empty."""
    user = create_user(
        db=db,
        username="randomtest",
        email="random@example.com",
        auth0_user_id="auth0|random123",
    )

    assert user.cryptpw != ""
    assert len(user.cryptpw) > 20


def test_create_user_firstname_surname_empty(db: Session):
    """Test that firstname and surname default to empty strings."""
    user = create_user(
        db=db,
        username="emptyname",
        email="empty@example.com",
        auth0_user_id="auth0|empty123",
    )

    assert user.firstname == ""
    assert user.surname == ""


def test_create_user_duplicate_username(db: Session):
    """Test that duplicate username is rejected."""
    username = "duplicateuser"
    email1 = "dup1@example.com"
    email2 = "dup2@example.com"
    auth0_id1 = "auth0|dup1"
    auth0_id2 = "auth0|dup2"

    # Create first user
    create_user(db=db, username=username, email=email1, auth0_user_id=auth0_id1)

    # Try to create second user with same username
    with pytest.raises(ValueError, match="Username .* already exists"):
        create_user(db=db, username=username, email=email2, auth0_user_id=auth0_id2)


def test_create_user_duplicate_email(db: Session):
    """Test that duplicate email is rejected."""
    username1 = "user1"
    username2 = "user2"
    email = "duplicate@example.com"
    auth0_id1 = "auth0|email1"
    auth0_id2 = "auth0|email2"

    # Create first user
    create_user(db=db, username=username1, email=email, auth0_user_id=auth0_id1)

    # Try to create second user with same email
    with pytest.raises(ValueError, match="Email .* already exists"):
        create_user(db=db, username=username2, email=email, auth0_user_id=auth0_id2)


def test_create_user_duplicate_auth0_user_id(db: Session):
    """Test that duplicate auth0_user_id is rejected."""
    username1 = "user1"
    username2 = "user2"
    email1 = "email1@example.com"
    email2 = "email2@example.com"
    auth0_user_id = "auth0|duplicate"

    # Create first user
    create_user(db=db, username=username1, email=email1, auth0_user_id=auth0_user_id)

    # Try to create second user with same auth0_user_id
    with pytest.raises(ValueError, match="Auth0 user ID .* already exists"):
        create_user(
            db=db, username=username2, email=email2, auth0_user_id=auth0_user_id
        )


def test_create_user_default_values(db: Session):
    """Test that default values are applied correctly."""
    user = create_user(
        db=db,
        username="defaultuser",
        email="default@example.com",
        auth0_user_id="auth0|default123",
    )

    assert user.email_valid == "Y"  # Auth0 verified
    assert user.email_ind == "N"  # Don't send emails by default
    assert user.public_ind == "N"  # Profile not public by default
    assert user.distance_ind == "K"  # Kilometres by default
    assert user.homepage == ""
    assert user.about == ""
    assert user.status_max == 0
    assert user.online_map_type == ""
    assert user.online_map_type2 == "lla"


def test_create_user_can_be_retrieved(db: Session):
    """Test that created user can be retrieved by various methods."""
    username = "retrieveuser"
    email = "retrieve@example.com"
    auth0_user_id = "auth0|retrieve123"

    created_user = create_user(
        db=db,
        username=username,
        email=email,
        auth0_user_id=auth0_user_id,
    )

    # Retrieve by auth0_user_id
    user_by_auth0 = get_user_by_auth0_id(db, auth0_user_id)
    assert user_by_auth0 is not None
    assert user_by_auth0.id == created_user.id

    # Retrieve by email
    user_by_email = get_user_by_email(db, email)
    assert user_by_email is not None
    assert user_by_email.id == created_user.id

    # Retrieve by username
    user_by_name = get_user_by_name(db, username)
    assert user_by_name is not None
    assert user_by_name.id == created_user.id
