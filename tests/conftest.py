"""
Test configuration and fixtures.
"""

import warnings

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# from app.core.security import get_password_hash  # No longer needed - using Unix crypt
from app.db.database import Base, get_db
from app.main import app
from app.models.user import TLog, User
from fastapi.testclient import TestClient

# from app.core.security import create_access_token  # Legacy JWT removed


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
    """Create test client with token validator patched for legacy tokens."""

    def _validate(token: str):
        # Simple mapping: 'legacy_user_<id>' -> legacy token for that user
        if token.startswith("legacy_user_"):
            try:
                user_id = int(token.split("_", 2)[2])
                return {"token_type": "legacy", "user_id": user_id}
            except Exception:
                return None
        # allow 'admin' legacy too if needed later
        if token == "legacy_admin":
            return {"token_type": "legacy", "user_id": 1000}
        return None

    monkeypatch.setattr(
        "app.core.security.auth0_validator.validate_auth0_token", _validate
    )

    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db):
    """Create a test user."""
    import crypt

    # Create Unix crypt hash for testing
    test_password = "testpassword123"
    cryptpw = crypt.crypt(test_password, "$1$testsalt$")

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
