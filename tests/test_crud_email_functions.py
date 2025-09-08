"""
Tests for CRUD email-related functions.
"""

from sqlalchemy.orm import Session

from app.crud.user import find_duplicate_emails, get_all_emails, get_users_by_email
from app.models.user import User


def test_get_all_emails_empty_database(db: Session):
    """Test get_all_emails with empty database."""
    emails = get_all_emails(db)
    assert emails == []


def test_get_all_emails_with_users(db: Session):
    """Test get_all_emails with users having emails."""
    users = [
        User(name="user1", email="user1@example.com"),
        User(name="user2", email="user2@example.com"),
        User(name="user3", email="user3@example.com"),
    ]
    for user in users:
        db.add(user)
    db.commit()

    emails = get_all_emails(db)
    assert len(emails) == 3
    assert "user1@example.com" in emails
    assert "user2@example.com" in emails
    assert "user3@example.com" in emails


def test_get_all_emails_with_none_emails(db: Session):
    """Test get_all_emails with users having None emails."""
    users = [
        User(name="user1", email="user1@example.com"),
        User(name="user2", email=None),
        User(name="user3", email="user3@example.com"),
    ]
    for user in users:
        db.add(user)
    db.commit()

    emails = get_all_emails(db)
    assert len(emails) == 2
    assert "user1@example.com" in emails
    assert "user3@example.com" in emails


def test_find_duplicate_emails_no_duplicates(db: Session):
    """Test find_duplicate_emails with no duplicates."""
    emails = ["user1@example.com", "user2@example.com", "user3@example.com"]
    duplicates = find_duplicate_emails(emails)
    assert duplicates == {}


def test_find_duplicate_emails_with_duplicates(db: Session):
    """Test find_duplicate_emails with duplicates."""
    emails = [
        "user@example.com",
        "User@Example.com",  # Case variation
        "admin@test.com",
        "Admin@Test.com",  # Case variation
        "unique@example.com",
    ]
    duplicates = find_duplicate_emails(emails)

    assert len(duplicates) == 2
    assert "user@example.com" in duplicates
    assert "admin@test.com" in duplicates

    # Check that case variations are grouped together
    assert set(duplicates["user@example.com"]) == {
        "user@example.com",
        "User@Example.com",
    }
    assert set(duplicates["admin@test.com"]) == {"admin@test.com", "Admin@Test.com"}


def test_find_duplicate_emails_with_whitespace(db: Session):
    """Test find_duplicate_emails with whitespace variations."""
    emails = [
        "user@example.com",
        " user@example.com ",  # Whitespace
        "user@example.com\t",  # Tab
        "admin@test.com",
    ]
    duplicates = find_duplicate_emails(emails)

    assert len(duplicates) == 1
    assert "user@example.com" in duplicates
    assert len(duplicates["user@example.com"]) == 3


def test_find_duplicate_emails_empty_emails(db: Session):
    """Test find_duplicate_emails with empty emails."""
    emails = ["", "user@example.com", "  ", "admin@test.com"]
    duplicates = find_duplicate_emails(emails)

    # Should only find duplicates for valid emails
    assert len(duplicates) == 0


def test_get_users_by_email_exact_match(db: Session):
    """Test get_users_by_email with exact match."""
    users = [
        User(name="user1", email="user@example.com"),
        User(name="user2", email="admin@test.com"),
        User(name="user3", email="user@example.com"),
    ]
    for user in users:
        db.add(user)
    db.commit()

    found_users = get_users_by_email(db, "user@example.com")
    assert len(found_users) == 2
    assert all(user.email == "user@example.com" for user in found_users)


def test_get_users_by_email_case_insensitive(db: Session):
    """Test get_users_by_email with case insensitive search."""
    users = [
        User(name="user1", email="user@example.com"),
        User(name="user2", email="User@Example.com"),
    ]
    for user in users:
        db.add(user)
    db.commit()

    found_users = get_users_by_email(db, "USER@EXAMPLE.COM")
    assert len(found_users) == 2
    assert all(user.email.lower() == "user@example.com" for user in found_users)


def test_get_users_by_email_no_match(db: Session):
    """Test get_users_by_email with no matching users."""
    users = [
        User(name="user1", email="user@example.com"),
        User(name="user2", email="admin@test.com"),
    ]
    for user in users:
        db.add(user)
    db.commit()

    found_users = get_users_by_email(db, "nonexistent@example.com")
    assert found_users == []


def test_get_users_by_email_empty_string(db: Session):
    """Test get_users_by_email with empty string."""
    users = [
        User(name="user1", email="user@example.com"),
        User(name="user2", email="admin@test.com"),
    ]
    for user in users:
        db.add(user)
    db.commit()

    found_users = get_users_by_email(db, "")
    assert found_users == []
