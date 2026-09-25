"""
PayPilot Global — Database engine and session management.
Supports MySQL (production) and SQLite (development fallback).
"""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from app.config import settings

# Configure connection arguments based on database type
connect_args = {}

if settings.database_url.startswith("sqlite"):
    # SQLite needs check_same_thread=False for FastAPI's thread pool
    connect_args["check_same_thread"] = False
    engine = create_engine(
        settings.database_url,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Enable WAL mode for SQLite concurrency
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # MySQL configuration (production)
    engine = create_engine(
        settings.database_url,
        pool_size=10,           # Number of connections to keep in pool
        max_overflow=20,        # Additional connections beyond pool_size
        pool_timeout=30,        # Timeout for getting connection from pool
        pool_recycle=3600,      # Recycle connections after 1 hour
        pool_pre_ping=True,     # Verify connection is alive before using
        echo=False,
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables. Call this on application startup."""
    Base.metadata.create_all(bind=engine)
