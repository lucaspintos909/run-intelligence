"""Database session management with SQLite WAL mode."""

import os
from typing import Generator

from sqlalchemy import event, create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from run_intelligence.config import Settings


_engine = None


def _get_engine():
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        settings = Settings()
        db_path = settings.DB_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )

        @event.listens_for(_engine, "connect")
        def _configure_sqlite_connection(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # Verify WAL mode is actually enabled
        with _engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode"))
            mode = result.fetchone()[0].lower()
            if mode != "wal":
                raise RuntimeError(f"Failed to enable WAL mode. Got: {mode}")

    return _engine


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session and handles cleanup."""
    engine = _get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database using Alembic migrations."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def create_session():
    """Create and return a new database session."""
    engine = _get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


# Backward-compatible alias
get_session = create_session