"""
Test configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User, TLog
from app.core.security import get_password_hash


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
def client():
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        admin_ind="N"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db):
    """Create a test admin user."""
    admin = User(
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword123"),
        admin_ind="Y"
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def test_tlog_entries(db):
    """Create test tlog entries."""
    entries = [
        TLog(trig_id=1),
        TLog(trig_id=1),
        TLog(trig_id=1),
        TLog(trig_id=2),
        TLog(trig_id=2),
    ]
    for entry in entries:
        db.add(entry)
    db.commit()
    return entries


@pytest.fixture
def user_token(client, test_user):
    """Get JWT token for test user."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_user.email, "password": "testpassword123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, test_admin_user):
    """Get JWT token for admin user."""
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": test_admin_user.email, "password": "adminpassword123"}
    )
    return response.json()["access_token"]
