"""
Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Lazy initialization - only create engine when first needed
_engine = None
_SessionLocal = None


def get_engine():
    """Get database engine, creating it if necessary."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.DEBUG,
        )
    return _engine


def get_session_local():
    """Get session maker, creating it if necessary."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal


Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
