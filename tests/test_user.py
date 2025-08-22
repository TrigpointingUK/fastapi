"""
Tests for user endpoints.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def test_get_user_not_found(client: TestClient, db: Session):
    """Test getting a non-existent user returns 404."""
    response = client.get("/api/v1/user/99999")
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
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",  # Public profile
    )
    db.add(user)
    db.commit()

    response = client.get("/api/v1/user/1")
    assert response.status_code == 200
    data = response.json()

    # Should include basic fields and email (public profile)
    assert data["id"] == 1
    assert data["name"] == "testuser"
    assert data["firstname"] == "Test"
    assert data["surname"] == "User"
    assert data["about"] == "Test user bio"
    assert data["email"] == "test@example.com"  # Public profile

    # Should NOT include private fields
    assert data["email_valid"] is None
    assert data["admin_ind"] is None
    assert data["public_ind"] is None


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
        admin_ind="N",
        email_valid="Y",
        public_ind="N",  # Private profile
    )
    db.add(user)
    db.commit()

    response = client.get("/api/v1/user/2")
    assert response.status_code == 200
    data = response.json()

    # Should include basic fields
    assert data["id"] == 2
    assert data["name"] == "privateuser"
    assert data["firstname"] == "Private"
    assert data["surname"] == "User"
    assert data["about"] == "Private user bio"

    # Should NOT include email or private fields
    assert data["email"] is None  # Private profile
    assert data["email_valid"] is None
    assert data["admin_ind"] is None
    assert data["public_ind"] is None


def test_get_user_by_name(client: TestClient, db: Session):
    """Test getting a user by username."""
    user = User(
        id=3,
        name="findme",
        firstname="Find",
        surname="Me",
        email="findme@example.com",
        cryptpw="$1$test$hash",
        about="Find me bio",
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    response = client.get("/api/v1/user/name/findme")
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == 3
    assert data["name"] == "findme"
    assert data["email"] == "findme@example.com"


def test_get_user_by_name_not_found(client: TestClient, db: Session):
    """Test getting a non-existent user by name returns 404."""
    response = client.get("/api/v1/user/name/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_search_users_by_name(client: TestClient, db: Session):
    """Test searching users by name pattern."""
    # Create test users
    users = [
        User(
            id=10,
            name="alice",
            firstname="Alice",
            surname="Smith",
            email="alice@test.com",
            cryptpw="$1$test$hash",
            about="",
            admin_ind="N",
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
            admin_ind="N",
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
            admin_ind="N",
            email_valid="Y",
            public_ind="Y",
        ),
    ]
    for user in users:
        db.add(user)
    db.commit()

    # Search for users containing "al"
    response = client.get("/api/v1/user/search/name?q=al")
    assert response.status_code == 200
    data = response.json()

    # Should find alice (contains "al") and charlie (contains "arlie")
    # Actually, let's search for something that matches both
    response = client.get("/api/v1/user/search/name?q=li")
    assert response.status_code == 200
    data = response.json()

    # Should find alice (contains "li") and charlie (contains "li")
    assert len(data) == 2
    names = [user["name"] for user in data]
    assert "alice" in names
    assert "charlie" in names


def test_get_users_count(client: TestClient, db: Session):
    """Test getting total user count."""
    # Add a few test users
    for i in range(5):
        user = User(
            id=100 + i,
            name=f"user{i}",
            firstname=f"User{i}",
            surname="Test",
            email=f"user{i}@test.com",
            cryptpw="$1$test$hash",
            about="",
            admin_ind="N",
            email_valid="Y",
            public_ind="Y",
        )
        db.add(user)
    db.commit()

    response = client.get("/api/v1/user/stats/count")
    assert response.status_code == 200
    data = response.json()

    assert "total_users" in data
    assert data["total_users"] >= 5  # At least the 5 we added
