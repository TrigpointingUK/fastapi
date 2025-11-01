"""
Test configuration and fixtures.
"""

import warnings

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# from api.core.security import get_password_hash  # No longer needed - using Unix crypt
from api.db.database import Base, get_db
from api.main import app
from api.models.user import TLog, User

# Legacy JWT tokens removed - Auth0 only


# Filter out deprecation warnings that are not actionable
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.*")
warnings.filterwarnings(
    "ignore", category=PendingDeprecationWarning, module="starlette.*"
)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="passlib.*")

# Test database URL (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(monkeypatch):
    """Create test client with token validator patched for Auth0 tokens only."""

    def _validate(token: str):
        # Auth0 test tokens only - no legacy tokens supported
        if token.startswith("auth0_user_"):
            try:
                user_id = int(token.split("_", 2)[2])
                return {"token_type": "auth0", "auth0_user_id": f"auth0|{user_id}"}
            except Exception:
                return None
        # Admin token
        if token == "auth0_admin":
            return {
                "token_type": "auth0",
                "auth0_user_id": "auth0|admin",
                "scope": "user:admin",
            }
        return None

    # Mock both token validation and Auth0 API calls
    monkeypatch.setattr(
        "api.core.security.auth0_validator.validate_auth0_token", _validate
    )

    # Mock the Auth0 service to prevent real API calls during tests
    def mock_find_user_by_auth0_id(auth0_user_id: str):
        # Return None to prevent Auth0 sync - we'll use existing database users
        return None

    monkeypatch.setattr(
        "api.services.auth0_service.auth0_service.find_user_by_auth0_id",
        mock_find_user_by_auth0_id,
    )

    # Also mock get_user_by_auth0_id to directly map auth0_user_id to database user_id
    def mock_get_user_by_auth0_id(db, auth0_user_id: str):
        if auth0_user_id.startswith("auth0|"):
            try:
                user_id = int(auth0_user_id.split("|")[1])
                from api.crud.user import get_user_by_id

                return get_user_by_id(db, user_id=user_id)
            except ValueError:
                pass
        return None

    monkeypatch.setattr("api.crud.user.get_user_by_auth0_id", mock_get_user_by_auth0_id)

    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db):
    """Create a test user."""
    from passlib.hash import des_crypt

    # Create Unix crypt hash for testing
    test_password = "testpassword123"
    cryptpw = des_crypt.hash(test_password)

    user = User(
        id=1000,  # Avoid conflicts with real data
        name="testuser",
        firstname="Test",
        surname="User",
        email="test@example.com",
        cryptpw=cryptpw,
        about="Test user for unit tests",
        email_valid="Y",
        public_ind="Y",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_tlog_entries(db):
    """Create test tlog entries."""
    from datetime import date, datetime, time

    entries = [
        TLog(
            trig_id=1,
            user_id=1000,
            date=date(2023, 12, 15),
            time=time(14, 30, 0),
            osgb_eastings=100000,
            osgb_northings=200000,
            osgb_gridref="TQ 00000 00000",
            fb_number="",
            condition="G",
            comment="Test log entry 1",
            score=7,
            ip_addr="127.0.0.1",
            source="W",
            upd_timestamp=datetime(2023, 12, 15, 14, 30, 0),
        ),
        TLog(
            trig_id=1,
            user_id=1000,
            date=date(2023, 12, 10),
            time=time(10, 15, 0),
            osgb_eastings=100000,
            osgb_northings=200000,
            osgb_gridref="TQ 00000 00000",
            fb_number="",
            condition="G",
            comment="Test log entry 2",
            score=8,
            ip_addr="127.0.0.1",
            source="W",
            upd_timestamp=datetime(2023, 12, 10, 10, 15, 0),
        ),
        TLog(
            trig_id=1,
            user_id=1000,
            date=date(2023, 12, 5),
            time=time(16, 45, 0),
            osgb_eastings=100000,
            osgb_northings=200000,
            osgb_gridref="TQ 00000 00000",
            fb_number="",
            condition="G",
            comment="Test log entry 3",
            score=9,
            ip_addr="127.0.0.1",
            source="W",
            upd_timestamp=datetime(2023, 12, 5, 16, 45, 0),
        ),
        TLog(
            trig_id=2,
            user_id=1001,
            date=date(2023, 11, 20),
            time=time(9, 15, 0),
            osgb_eastings=150000,
            osgb_northings=250000,
            osgb_gridref="TQ 50000 50000",
            fb_number="",
            condition="G",
            comment="Test log entry 4",
            score=6,
            ip_addr="127.0.0.1",
            source="W",
            upd_timestamp=datetime(2023, 11, 20, 9, 15, 0),
        ),
        TLog(
            trig_id=2,
            user_id=1001,
            date=date(2023, 11, 15),
            time=time(11, 30, 0),
            osgb_eastings=150000,
            osgb_northings=250000,
            osgb_gridref="TQ 50000 50000",
            fb_number="",
            condition="G",
            comment="Test log entry 5",
            score=7,
            ip_addr="127.0.0.1",
            source="W",
            upd_timestamp=datetime(2023, 11, 15, 11, 30, 0),
        ),
    ]
    for entry in entries:
        db.add(entry)
    db.commit()
    return entries
