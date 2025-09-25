"""
Tests for user endpoints.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User


def test_get_user_not_found(client: TestClient, db: Session):
    """Test getting a non-existent user returns 404."""
    response = client.get(f"{settings.API_V1_STR}/users/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_public_unauthenticated(client: TestClient, db: Session):
    """Test getting a public user while unauthenticated."""
    # Create a test user with public profile
    user = User(
        id=1,
        name="testuser",
        firstname="Test",
        surname="User",
        email="test@example.com",
        cryptpw="$1$test$hash",
        about="Test user bio",
        email_valid="Y",
        public_ind="Y",  # Public profile
    )
    db.add(user)
    db.commit()

    response = client.get(f"{settings.API_V1_STR}/users/1")
    assert response.status_code == 200
    data = response.json()

    # Should include basic fields and public email in base response
    assert data["id"] == 1
    assert data["name"] == "testuser"
    assert data["firstname"] == "Test"
    assert data["surname"] == "User"
    assert data["about"] == "Test user bio"
    # Email field deprecated - no longer returned


def test_get_user_private_unauthenticated(client: TestClient, db: Session):
    """Test getting a private user while unauthenticated."""
    # Create a test user with private profile
    user = User(
        id=2,
        name="privateuser",
        firstname="Private",
        surname="User",
        email="private@example.com",
        cryptpw="$1$test$hash",
        about="Private user bio",
        email_valid="Y",
        public_ind="N",  # Private profile
    )
    db.add(user)
    db.commit()

    response = client.get(f"{settings.API_V1_STR}/users/2")
    assert response.status_code == 200
    data = response.json()

    # Should include basic fields
    assert data["id"] == 2
    assert data["name"] == "privateuser"
    assert data["firstname"] == "Private"
    assert data["surname"] == "User"
    assert data["about"] == "Private user bio"

    # Email field deprecated - no longer returned


# removed name lookup endpoint tests


def test_list_users_envelope_and_filter(client: TestClient, db: Session):
    """Test users list envelope, pagination, and name filter."""
    users = [
        User(
            id=10,
            name="alice",
            firstname="Alice",
            surname="Smith",
            email="alice@test.com",
            cryptpw="$1$test$hash",
            about="",
            email_valid="Y",
            public_ind="Y",
        ),
        User(
            id=11,
            name="bob",
            firstname="Bob",
            surname="Jones",
            email="bob@test.com",
            cryptpw="$1$test$hash",
            about="",
            email_valid="Y",
            public_ind="Y",
        ),
        User(
            id=12,
            name="charlie",
            firstname="Charlie",
            surname="Brown",
            email="charlie@test.com",
            cryptpw="$1$test$hash",
            about="",
            email_valid="Y",
            public_ind="Y",
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()

    # No filter (all)
    resp = client.get(f"{settings.API_V1_STR}/users")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "pagination" in body and "links" in body
    assert len(body["items"]) >= 3

    # Filter by name contains 'li'
    resp = client.get(f"{settings.API_V1_STR}/users?name=li")
    assert resp.status_code == 200
    body = resp.json()
    names = [u["name"] for u in body["items"]]
    assert "alice" in names and "charlie" in names

    # Envelope structure with pagination
    resp = client.get(f"{settings.API_V1_STR}/users?limit=1&skip=0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["pagination"]["limit"] == 1
    assert body["pagination"]["offset"] == 0
