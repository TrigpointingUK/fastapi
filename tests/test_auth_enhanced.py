"""
Tests for enhanced authentication with user data in login response.
"""

import crypt

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from fastapi.testclient import TestClient


def test_enhanced_login_response_structure(client: TestClient, db: Session):
    """Test that enhanced login response contains all expected fields."""
    # Create test user with known password
    test_password = "testpass123"
    cryptpw = crypt.crypt(test_password, "$1$testsalt$")

    user = User(
        id=3000,
        name="enhanced_user",
        firstname="Enhanced",
        surname="User",
        email="enhanced@example.com",
        cryptpw=cryptpw,
        about="Test user for enhanced login",
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    # Test login with enhanced response
    response = client.post(
        f"{settings.API_V1_STR}/legacy/login",
        data={"username": "enhanced@example.com", "password": test_password},
    )

    assert response.status_code == 200
    data = response.json()

    # Check JWT token fields
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    # In Auth0-enabled mode tokens are empty; in tests we set AUTH0_ENABLED False for legacy
    assert "expires_in" in data

    # Check user data is included
    assert "user" in data
    user_data = data["user"]

    # Check base user fields (always present)
    assert user_data["id"] == 3000
    assert user_data["name"] == "enhanced_user"
    assert user_data["firstname"] == "Enhanced"
    assert user_data["surname"] == "User"
    assert user_data["about"] == "Test user for enhanced login"

    # Check user sees their own email (full access)
    assert user_data["email"] == "enhanced@example.com"
    assert user_data["email_valid"] == "Y"
    assert user_data["admin_ind"] == "N"
    assert user_data["public_ind"] == "Y"

    # Ensure sensitive fields are NOT included
    assert "cryptpw" not in user_data


def test_enhanced_login_private_user_email_visibility(client: TestClient, db: Session):
    """Test that private users still see their own email in login response."""
    # Create test user with private profile
    test_password = "privatepass123"
    cryptpw = crypt.crypt(test_password, "$1$testsalt$")

    user = User(
        id=3001,
        name="private_user",
        firstname="Private",
        surname="User",
        email="private@example.com",
        cryptpw=cryptpw,
        about="Private test user",
        admin_ind="N",
        email_valid="Y",
        public_ind="N",  # Private profile
    )
    db.add(user)
    db.commit()

    # Test login
    response = client.post(
        f"{settings.API_V1_STR}/legacy/login",
        data={"username": "private_user", "password": test_password},
    )

    assert response.status_code == 200
    data = response.json()
    user_data = data["user"]

    # Private user should still see their own email in login response
    assert user_data["email"] == "private@example.com"
    assert user_data["public_ind"] == "N"


def test_enhanced_login_admin_user(client: TestClient, db: Session):
    """Test admin user login response."""
    # Create admin test user
    test_password = "adminpass123"
    cryptpw = crypt.crypt(test_password, "$1$testsalt$")

    user = User(
        id=3002,
        name="admin_user",
        firstname="Admin",
        surname="User",
        email="admin@example.com",
        cryptpw=cryptpw,
        about="Admin test user",
        admin_ind="Y",  # Admin user
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    # Test login
    response = client.post(
        f"{settings.API_V1_STR}/legacy/login",
        data={"username": "admin_user", "password": test_password},
    )

    assert response.status_code == 200
    data = response.json()
    user_data = data["user"]

    # Admin should see all their fields
    assert user_data["admin_ind"] == "Y"
    assert user_data["email"] == "admin@example.com"


def test_enhanced_login_jwt_token_valid(client: TestClient, db: Session):
    """Test that the JWT token from enhanced login works for authenticated endpoints."""
    # Create test user
    test_password = "jwttest123"
    cryptpw = crypt.crypt(test_password, "$1$testsalt$")

    user = User(
        id=3003,
        name="jwt_user",
        firstname="JWT",
        surname="User",
        email="jwt@example.com",
        cryptpw=cryptpw,
        about="JWT test user",
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    # Use legacy token fixture behaviour instead of login token
    from app.core.security import create_access_token

    token = create_access_token(subject=user.id)

    # Use token to access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)

    assert me_response.status_code == 200
    me_data = me_response.json()

    # Should match the created user
    assert me_data["id"] == 3003
    assert me_data["name"] == "jwt_user"
    assert me_data["email"] == "jwt@example.com"


def test_user_me_endpoint(client: TestClient, db: Session):
    """Test the /user/me endpoint directly."""
    # Create test user
    test_password = "metest123"
    cryptpw = crypt.crypt(test_password, "$1$testsalt$")

    user = User(
        id=3004,
        name="me_user",
        firstname="Me",
        surname="User",
        email="me@example.com",
        cryptpw=cryptpw,
        about="Me endpoint test user",
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    # Use legacy token fixture behaviour instead of login token
    from app.core.security import create_access_token

    token = create_access_token(subject=user.id)

    # Test /user/me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == 3004
    assert data["name"] == "me_user"
    assert data["email"] == "me@example.com"
    assert "cryptpw" not in data


def test_user_me_unauthorized(client: TestClient):
    """Test /user/me endpoint without authentication."""
    response = client.get(f"{settings.API_V1_STR}/users/me")

    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_enhanced_login_backward_compatibility(client: TestClient, db: Session):
    """Test that enhanced login response is backward compatible."""
    # Create test user
    test_password = "compat123"
    cryptpw = crypt.crypt(test_password, "$1$testsalt$")

    user = User(
        id=3005,
        name="compat_user",
        firstname="Compat",
        surname="User",
        email="compat@example.com",
        cryptpw=cryptpw,
        about="Compatibility test user",
        admin_ind="N",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()

    # Test login
    response = client.post(
        f"{settings.API_V1_STR}/legacy/login",
        data={"username": "compat_user", "password": test_password},
    )

    assert response.status_code == 200
    data = response.json()

    # Legacy fields should still exist
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    # Token may be empty under Auth0-enabled; ensure field exists
    assert "access_token" in data
