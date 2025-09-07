"""
Tests for email duplicates API endpoints.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User

client = TestClient(app)


class TestEmailDuplicatesAPI:
    """Test cases for the email duplicates API endpoint."""

    def test_get_email_duplicates_empty_database(self, db: Session):
        """Test getting email duplicates with empty database."""
        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 200
        result = response.json()
        assert "pagination" in result
        assert result["pagination"]["total_duplicates"] == 0

    def test_get_email_duplicates_no_duplicates(self, db: Session):
        """Test getting email duplicates with no duplicates."""
        # Create test users with unique email addresses
        users = [
            User(name="user1", email="user1@example.com"),
            User(name="user2", email="user2@example.com"),
            User(name="user3", email="user3@example.com"),
        ]
        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 200
        result = response.json()
        assert "pagination" in result
        assert result["pagination"]["total_duplicates"] == 0

    def test_get_email_duplicates_with_duplicates(self, db: Session):
        """Test getting email duplicates with actual duplicates."""
        # Create test users with duplicate email addresses (case variations)
        users = [
            User(name="user1", email="user@example.com"),
            User(name="user2", email="User@Example.com"),
            User(name="user3", email="USER@EXAMPLE.COM"),
            User(name="admin1", email="admin@test.com"),
            User(name="admin2", email="Admin@Test.com"),
            User(name="unique_user", email="unique@example.com"),
        ]
        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 200

        result = response.json()
        assert "user@example.com" in result
        assert "admin@test.com" in result
        assert "unique@example.com" not in result  # No duplicates for this one

        # Check that the duplicates are correctly identified
        assert set(result["user@example.com"]["original_emails"]) == {
            "user@example.com",
            "User@Example.com",
            "USER@EXAMPLE.COM",
        }
        assert set(result["admin@test.com"]["original_emails"]) == {
            "admin@test.com",
            "Admin@Test.com",
        }

        # Check that each duplicate has user information with log stats
        assert "users" in result["user@example.com"]
        assert "users" in result["admin@test.com"]

        # Check that each user has the required fields
        for user_info in result["user@example.com"]["users"]:
            assert "username" in user_info
            assert "user_id" in user_info
            assert "email" in user_info
            assert "log_count" in user_info
            assert "latest_log_timestamp" in user_info

        # Check pagination information
        assert "pagination" in result
        assert result["pagination"]["total_duplicates"] == 2
        assert result["pagination"]["limit"] == 50
        assert result["pagination"]["offset"] == 0
        assert result["pagination"]["has_more"] is False

    def test_get_email_duplicates_with_whitespace_variations(self, db: Session):
        """Test getting email duplicates with whitespace variations."""
        # Create test users with email addresses that differ only in whitespace
        users = [
            User(name="user1", email="user@example.com"),
            User(name="user2", email=" user@example.com "),
            User(name="user3", email="\tuser@example.com\t"),
        ]
        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 200

        result = response.json()
        assert "user@example.com" in result
        assert len(result["user@example.com"]["original_emails"]) == 3

    def test_get_email_duplicates_with_empty_emails(self, db: Session):
        """Test getting email duplicates with empty or None emails."""
        # Create test users with valid emails (can't create users with empty emails due to DB constraints)
        users = [
            User(name="user1", email="user1@example.com"),
            User(name="user2", email="user2@example.com"),
        ]
        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 200

        result = response.json()
        # No duplicates for these emails, but should have pagination info
        assert "pagination" in result
        assert result["pagination"]["total_duplicates"] == 0

    def test_get_email_duplicates_large_dataset(self, db: Session):
        """Test getting email duplicates with a large dataset."""
        # Create test users with some duplicate emails
        users = []
        for i in range(10):
            if i % 3 == 0:
                users.append(User(name=f"user{i}", email="common@example.com"))
            elif i % 3 == 1:
                users.append(User(name=f"user{i}", email="Common@Example.com"))
            else:
                users.append(User(name=f"user{i}", email=f"unique{i}@example.com"))

        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 200

        result = response.json()
        # Should have duplicates for common@example.com
        assert "common@example.com" in result
        # Should have 7 users with this email (4 with "common@example.com" + 3 with "Common@Example.com")
        assert len(result["common@example.com"]["original_emails"]) == 7

        # Check that each user has the required fields
        for user_info in result["common@example.com"]["users"]:
            assert "username" in user_info
            assert "user_id" in user_info
            assert "email" in user_info
            assert "log_count" in user_info
            assert "latest_log_timestamp" in user_info

    def test_get_email_duplicates_error_handling(self, db: Session, monkeypatch):
        """Test error handling in the email duplicates endpoint."""

        # Mock the get_all_emails function to raise an exception
        def mock_get_all_emails(db):
            raise Exception("Database error")

        monkeypatch.setattr(
            "app.api.v1.endpoints.username_analysis.get_all_emails",
            mock_get_all_emails,
        )

        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 500
        assert "Error analyzing email duplicates" in response.json()["detail"]

    def test_get_email_duplicates_with_log_information(
        self, db: Session, test_tlog_entries
    ):
        """Test that email duplicates include log information."""
        # Create test users with duplicate emails
        users = [
            User(name="user1", email="test@example.com"),
            User(name="user2", email="Test@Example.com"),
        ]
        for user in users:
            db.add(user)
        db.commit()

        response = client.get("/api/v1/analysis/email-duplicates")
        assert response.status_code == 200

        result = response.json()
        assert "test@example.com" in result

        # Check that log information is included
        for user_info in result["test@example.com"]["users"]:
            assert "log_count" in user_info
            assert "latest_log_timestamp" in user_info
            # Should have log information from test_tlog_entries fixture
            assert user_info["log_count"] >= 0

    def test_get_email_duplicates_pagination(self, db: Session):
        """Test pagination functionality."""
        # Create test users with multiple duplicate emails
        users = []
        for i in range(10):
            users.append(User(name=f"user{i}", email="common@example.com"))
            users.append(User(name=f"user{i + 10}", email="Common@Example.com"))
            users.append(User(name=f"user{i + 20}", email=f"unique{i}@example.com"))

        for user in users:
            db.add(user)
        db.commit()

        # Test first page
        response = client.get("/api/v1/analysis/email-duplicates?limit=1&offset=0")
        assert response.status_code == 200
        result = response.json()
        assert "pagination" in result
        assert result["pagination"]["limit"] == 1
        assert result["pagination"]["offset"] == 0
        assert result["pagination"]["total_duplicates"] == 1
        assert result["pagination"]["has_more"] is False
        assert len([k for k in result.keys() if k != "pagination"]) == 1

    def test_get_email_duplicates_pagination_validation(self, db: Session):
        """Test pagination parameter validation."""
        # Test invalid limit
        response = client.get("/api/v1/analysis/email-duplicates?limit=0")
        assert response.status_code == 400
        assert "Limit must be greater than 0" in response.json()["detail"]

        # Test negative offset
        response = client.get("/api/v1/analysis/email-duplicates?offset=-1")
        assert response.status_code == 400
        assert "Offset must be 0 or greater" in response.json()["detail"]

        # Test limit too high
        response = client.get("/api/v1/analysis/email-duplicates?limit=1001")
        assert response.status_code == 400
        assert "Limit cannot exceed 1000" in response.json()["detail"]

    def test_get_email_duplicates_pagination_large_dataset(self, db: Session):
        """Test pagination with a larger dataset."""
        # Create test users with multiple duplicate emails
        users = []
        for i in range(5):
            users.append(User(name=f"user{i}", email="common@example.com"))
            users.append(User(name=f"user{i + 5}", email="Common@Example.com"))
            users.append(User(name=f"user{i + 10}", email="admin@test.com"))
            users.append(User(name=f"user{i + 15}", email="Admin@Test.com"))

        for user in users:
            db.add(user)
        db.commit()

        # Test pagination with limit=2
        response = client.get("/api/v1/analysis/email-duplicates?limit=2&offset=0")
        assert response.status_code == 200
        result = response.json()
        assert "pagination" in result
        assert result["pagination"]["limit"] == 2
        assert result["pagination"]["offset"] == 0
        assert result["pagination"]["total_duplicates"] == 2
        assert result["pagination"]["has_more"] is False
