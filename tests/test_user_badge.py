"""
Tests for user badge endpoint.
"""

from datetime import date, time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import TLog, User


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
    db.commit()

    # Add some test logs for the user
    log1 = TLog(
        id=1,
        user_id=1,
        trig_id=1,
        date=date(2023, 1, 1),
        time=time(12, 0, 0),
        osgb_eastings=0,
        osgb_northings=0,
        osgb_gridref="AA 00000 00000",
        fb_number="",
        condition="G",
        comment="",
        score=0,
        ip_addr="",
        source="W",
    )
    log2 = TLog(
        id=2,
        user_id=1,
        trig_id=2,
        date=date(2023, 1, 2),
        time=time(12, 0, 0),
        osgb_eastings=0,
        osgb_northings=0,
        osgb_gridref="AA 00000 00000",
        fb_number="",
        condition="G",
        comment="",
        score=0,
        ip_addr="",
        source="W",
    )
    log3 = TLog(
        id=3,
        user_id=1,
        trig_id=1,
        date=date(2023, 1, 3),
        time=time(12, 0, 0),
        osgb_eastings=0,
        osgb_northings=0,
        osgb_gridref="AA 00000 00000",
        fb_number="",
        condition="G",
        comment="",
        score=0,
        ip_addr="",
        source="W",
    )

    db.add_all([log1, log2, log3])
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

    response = client.get(f"{settings.API_V1_STR}/users/2/badge?scale=1.0")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "user_2_badge.png" in response.headers.get("content-disposition", "")

    # Verify we got PNG data
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_get_user_badge_transparent_false(client: TestClient, db: Session):
    """Test getting a badge with explicit parameter still returns PNG."""
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

    response = client.get(f"{settings.API_V1_STR}/users/3/badge?scale=1.0")
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
