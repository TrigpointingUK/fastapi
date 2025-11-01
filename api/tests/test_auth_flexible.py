# """
# Tests for flexible authentication (email or username).
# """
#
# import crypt
#
# from sqlalchemy.orm import Session
#
# from api.core.config import settings
# from api.models.user import User
# from fastapi.testclient import TestClient
#
#
# def test_login_with_email_success(client: TestClient, db: Session):
#     """Test login using email address."""
#     # Create test user with known password
#     test_password = "testpass123"
#     cryptpw = crypt.crypt(test_password, "$1$testsalt$")
#
#     user = User(
#         id=2000,
#         name="testuser_email",
#         firstname="Test",
#         surname="User",
#         email="test.email@example.com",
#         cryptpw=cryptpw,
#         about="Test user for email login",
#         email_valid="Y",
#         public_ind="Y",
#     )
#     db.add(user)
#     db.commit()
#
#     # Test login with email
#     response = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "test.email@example.com", "password": test_password},
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert "access_token" in data
#     assert data["token_type"] == "bearer"
#
#
# def test_login_with_username_success(client: TestClient, db: Session):
#     """Test login using username."""
#     # Create test user with known password
#     test_password = "testpass456"
#     cryptpw = crypt.crypt(test_password, "$1$testsalt$")
#
#     user = User(
#         id=2001,
#         name="testuser_name",
#         firstname="Test",
#         surname="User",
#         email="different.email@example.com",
#         cryptpw=cryptpw,
#         about="Test user for username login",
#         email_valid="Y",
#         public_ind="Y",
#     )
#     db.add(user)
#     db.commit()
#
#     # Test login with username
#     response = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "testuser_name", "password": test_password},
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert "access_token" in data
#     assert data["token_type"] == "bearer"
#
#
# def test_login_with_email_wrong_password(client: TestClient, db: Session):
#     """Test login with email but wrong password."""
#     # Create test user
#     test_password = "correctpass"
#     cryptpw = crypt.crypt(test_password, "$1$testsalt$")
#
#     user = User(
#         id=2002,
#         name="testuser_wrong",
#         firstname="Test",
#         surname="User",
#         email="wrong.pass@example.com",
#         cryptpw=cryptpw,
#         about="Test user for wrong password",
#         email_valid="Y",
#         public_ind="Y",
#     )
#     db.add(user)
#     db.commit()
#
#     # Test login with wrong password
#     response = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "wrong.pass@example.com", "password": "wrongpassword"},
#     )
#     assert response.status_code == 401
#     assert "Incorrect username/email or password" in response.json()["detail"]
#
#
# def test_login_with_username_wrong_password(client: TestClient, db: Session):
#     """Test login with username but wrong password."""
#     # Create test user
#     test_password = "correctpass"
#     cryptpw = crypt.crypt(test_password, "$1$testsalt$")
#
#     user = User(
#         id=2003,
#         name="testuser_wrong2",
#         firstname="Test",
#         surname="User",
#         email="another.wrong@example.com",
#         cryptpw=cryptpw,
#         about="Test user for wrong password via username",
#         email_valid="Y",
#         public_ind="Y",
#     )
#     db.add(user)
#     db.commit()
#
#     # Test login with wrong password
#     response = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "testuser_wrong2", "password": "wrongpassword"},
#     )
#     assert response.status_code == 401
#     assert "Incorrect username/email or password" in response.json()["detail"]
#
#
# def test_login_nonexistent_email(client: TestClient, db: Session):
#     """Test login with non-existent email."""
#     response = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "nonexistent@example.com", "password": "anypassword"},
#     )
#     assert response.status_code == 401
#     assert "Incorrect username/email or password" in response.json()["detail"]
#
#
# def test_login_nonexistent_username(client: TestClient, db: Session):
#     """Test login with non-existent username."""
#     response = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "nonexistentuser", "password": "anypassword"},
#     )
#     assert response.status_code == 401
#     assert "Incorrect username/email or password" in response.json()["detail"]
#
#
# def test_login_edge_case_username_with_at(client: TestClient, db: Session):
#     """Test login with username that contains @ symbol."""
#     # Create user with @ in username (edge case)
#     test_password = "edgecase123"
#     cryptpw = crypt.crypt(test_password, "$1$testsalt$")
#
#     user = User(
#         id=2004,
#         name="user@company",  # Username with @ symbol
#         firstname="Edge",
#         surname="Case",
#         email="edge.case@example.com",
#         cryptpw=cryptpw,
#         about="Edge case user with @ in username",
#         email_valid="Y",
#         public_ind="Y",
#     )
#     db.add(user)
#     db.commit()
#
#     # Should still work - fallback logic handles this
#     response = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "user@company", "password": test_password},
#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert "access_token" in data
#
#
# def test_login_same_user_both_methods(client: TestClient, db: Session):
#     """Test that same user can login with both email and username."""
#     # Create test user
#     test_password = "bothways123"
#     cryptpw = crypt.crypt(test_password, "$1$testsalt$")
#
#     user = User(
#         id=2005,
#         name="flexibleuser",
#         firstname="Flexible",
#         surname="User",
#         email="flexible@example.com",
#         cryptpw=cryptpw,
#         about="User who can login both ways",
#         email_valid="Y",
#         public_ind="Y",
#     )
#     db.add(user)
#     db.commit()
#
#     # Test login with email
#     response1 = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "flexible@example.com", "password": test_password},
#     )
#     assert response1.status_code == 200
#
#     # Test login with username
#     response2 = client.post(
#         f"{settings.API_V1_STR}/legacy/login",
#         data={"username": "flexibleuser", "password": test_password},
#     )
#     assert response2.status_code == 200
#
#     # Both should return valid tokens
#     token1 = response1.json()["access_token"]
#     token2 = response2.json()["access_token"]
#     assert token1 is not None
#     assert token2 is not None
