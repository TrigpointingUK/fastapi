"""
Tests for user badge endpoint.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.user import TLog
from app.models.user import User


def test_get_user_badge_not_found(client: TestClient, db: Session):
    """Test getting a badge for non-existent user returns 404."""
    response = client.get(f"{settings.API_V1_STR}/users/99999/badge")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_badge_success(client: TestClient, db: Session):
    """Test getting a badge for an existing user."""
    # Create a test user
    user = User(
        id=1,
        name="testuser",
        firstname="Test",
        surname="User",
        email="test@example.com",
        cryptpw="$1$test$hash",
        about="Test user bio",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)

    # Add some test logs for the user
    log1 = TLog(id=1, user_id=1, trig_id=1, logged="2023-01-01", status=1)
    log2 = TLog(id=2, user_id=1, trig_id=2, logged="2023-01-02", status=1)
    log3 = TLog(
        id=3, user_id=1, trig_id=1, logged="2023-01-03", status=2
    )  # Same trig, different status

    db.add(log1)
    db.add(log2)
    db.add(log3)
    db.commit()

    response = client.get(f"{settings.API_V1_STR}/users/1/badge")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "user_1_badge.png" in response.headers.get("content-disposition", "")

    # Verify we got PNG data
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_get_user_badge_transparent(client: TestClient, db: Session):
    """Test getting a badge with transparent background."""
    # Create a test user
    user = User(
        id=2,
        name="transparentuser",
        firstname="Transparent",
        surname="User",
        email="transparent@example.com",
        cryptpw="$1$test$hash",
        about="Transparent badge user",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    response = client.get(f"{settings.API_V1_STR}/users/2/badge?transparent=true")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "user_2_badge.png" in response.headers.get("content-disposition", "")

    # Verify we got PNG data
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_get_user_badge_transparent_false(client: TestClient, db: Session):
    """Test getting a badge with explicit transparent=false."""
    # Create a test user
    user = User(
        id=3,
        name="opaqueuser",
        firstname="Opaque",
        surname="User",
        email="opaque@example.com",
        cryptpw="$1$test$hash",
        about="Opaque badge user",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    response = client.get(f"{settings.API_V1_STR}/users/3/badge?transparent=false")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "user_3_badge.png" in response.headers.get("content-disposition", "")

    # Verify we got PNG data
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_get_user_badge_no_logs(client: TestClient, db: Session):
    """Test getting a badge for user with no logs."""
    # Create a test user with no logs
    user = User(
        id=4,
        name="nologsuser",
        firstname="NoLogs",
        surname="User",
        email="nologs@example.com",
        cryptpw="$1$test$hash",
        about="User with no logs",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    response = client.get(f"{settings.API_V1_STR}/users/4/badge")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Verify we got PNG data
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
