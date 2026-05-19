"""Shared test fixtures."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from run_intelligence.db.models import Base
from run_intelligence.db.repository import (
    AuditLogRepository,
    RunRepository,
    HealthLogRepository,
    ConversationRepository,
    RunnerMetricsRepository,
)


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database engine for testing."""
    from sqlalchemy import event

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_wal_mode(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test session bound to the in-memory database."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def audit_logger(test_session):
    """Create an AuditLogRepository instance for testing."""
    return AuditLogRepository(session=test_session)


@pytest.fixture
def run_repo(test_session, audit_logger):
    """Create a RunRepository instance for testing."""
    return RunRepository(session=test_session, audit_logger=audit_logger)


@pytest.fixture
def health_log_repo(test_session, audit_logger):
    """Create a HealthLogRepository instance for testing."""
    return HealthLogRepository(session=test_session, audit_logger=audit_logger)


@pytest.fixture
def conversation_repo(test_session, audit_logger):
    """Create a ConversationRepository instance for testing."""
    return ConversationRepository(session=test_session, audit_logger=audit_logger)


@pytest.fixture
def runner_metrics_repo(test_session, audit_logger):
    """Create a RunnerMetricsRepository instance for testing."""
    return RunnerMetricsRepository(session=test_session, audit_logger=audit_logger)


@pytest.fixture
def sample_run_data():
    """Sample run data for testing."""
    return {
        "file_path": "/path/to/test.fit",
        "raw_metrics_json": '{"pace": 5.5, "hr": 145, "cadence": 170}',
        "derived_metrics_json": '{"vo2max": 45.2, "vdot": 42.1}',
        "data_quality_flags_json": '{"hr_artifacts": false, "gps_drift": 0.02}',
    }


@pytest.fixture
def sample_health_log_data():
    """Sample health log data for testing."""
    return {
        "entry_date": date(2026, 5, 18),
        "peak_flow": 450,
        "sleep_quality": 3,
        "post_run_rpe": 12,
        "asthma_symptoms": 1,
        "saba_use": False,
        "notes": "Felt good today",
    }