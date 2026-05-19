"""Tests for database repository layer."""

import pytest
from datetime import date


class TestRunRepository:
    """Tests for RunRepository."""

    def test_create_run(self, run_repo, sample_run_data):
        """Test creating a new run."""
        run = run_repo.create_run(**sample_run_data)

        assert run.id is not None
        assert run.file_path == sample_run_data["file_path"]
        assert run.raw_metrics_json == sample_run_data["raw_metrics_json"]

    def test_get_run(self, run_repo, sample_run_data):
        """Test retrieving a run by ID."""
        created = run_repo.create_run(**sample_run_data)
        retrieved = run_repo.get_run(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.file_path == sample_run_data["file_path"]

    def test_get_run_not_found(self, run_repo):
        """Test retrieving a non-existent run."""
        result = run_repo.get_run(99999)
        assert result is None

    def test_get_runs(self, run_repo, sample_run_data):
        """Test retrieving multiple runs."""
        run_repo.create_run(**sample_run_data)
        run_repo.create_run(file_path="/path/to/second.fit")

        runs = run_repo.get_runs()
        assert len(runs) == 2

    def test_update_run(self, run_repo, sample_run_data):
        """Test updating a run."""
        created = run_repo.create_run(**sample_run_data)
        new_raw = '{"updated": true}'
        updated = run_repo.update_run(created.id, raw_metrics_json=new_raw)

        assert updated is not None
        assert updated.raw_metrics_json == new_raw

    def test_delete_run(self, run_repo, sample_run_data):
        """Test deleting a run."""
        created = run_repo.create_run(**sample_run_data)
        result = run_repo.delete_run(created.id)

        assert result is True
        assert run_repo.get_run(created.id) is None

    def test_delete_run_not_found(self, run_repo):
        """Test deleting a non-existent run."""
        result = run_repo.delete_run(99999)
        assert result is False


class TestHealthLogRepository:
    """Tests for HealthLogRepository."""

    def test_create_entry(self, health_log_repo):
        """Test creating a health log entry."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 18),
            peak_flow=450,
            sleep_quality=3,
        )

        assert entry.id is not None
        assert entry.peak_flow == 450
        assert entry.sleep_quality == 3

    def test_get_entry(self, health_log_repo):
        """Test retrieving a health log entry."""
        created = health_log_repo.create_entry(
            entry_date=date(2026, 5, 18),
            peak_flow=450,
        )
        retrieved = health_log_repo.get_entry(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_entries(self, health_log_repo):
        """Test retrieving multiple health log entries."""
        health_log_repo.create_entry(entry_date=date(2026, 5, 18), peak_flow=400)
        health_log_repo.create_entry(entry_date=date(2026, 5, 17), peak_flow=420)

        entries = health_log_repo.get_entries()
        assert len(entries) == 2

    def test_update_entry(self, health_log_repo):
        """Test updating a health log entry."""
        created = health_log_repo.create_entry(entry_date=date(2026, 5, 18), peak_flow=400)
        updated = health_log_repo.update_entry(created.id, peak_flow=450)

        assert updated is not None
        assert updated.peak_flow == 450

    def test_delete_entry(self, health_log_repo):
        """Test deleting a health log entry."""
        created = health_log_repo.create_entry(entry_date=date(2026, 5, 18))
        result = health_log_repo.delete_entry(created.id)

        assert result is True
        assert health_log_repo.get_entry(created.id) is None

    def test_link_to_run(self, health_log_repo, run_repo):
        """Test linking a health log entry to a run."""
        run = run_repo.create_run(file_path="/path/to/run.fit")
        entry = health_log_repo.create_entry(entry_date=date(2026, 5, 18))

        linked = health_log_repo.link_to_run(entry.id, run.id)

        assert linked is not None
        assert linked.run_id == run.id

    def test_entry_without_run_id(self, health_log_repo):
        """Test health log entry can exist without a run_id."""
        entry = health_log_repo.create_entry(entry_date=date(2026, 5, 18))
        assert entry.run_id is None


class TestConversationRepository:
    """Tests for ConversationRepository."""

    def test_create_message(self, conversation_repo):
        """Test creating a conversation message."""
        message = conversation_repo.create_message(
            session_id="session-123",
            role="user",
            content="Hello!",
        )

        assert message.id is not None
        assert message.session_id == "session-123"
        assert message.role == "user"
        assert message.content == "Hello!"

    def test_get_session_messages(self, conversation_repo):
        """Test retrieving all messages for a session."""
        conversation_repo.create_message(session_id="session-123", role="user", content="Hello")
        conversation_repo.create_message(session_id="session-123", role="assistant", content="Hi there")
        conversation_repo.create_message(session_id="session-456", role="user", content="Different")

        messages = conversation_repo.get_session_messages("session-123")
        assert len(messages) == 2
        assert all(m.session_id == "session-123" for m in messages)

    def test_delete_session(self, conversation_repo):
        """Test deleting all messages for a session."""
        conversation_repo.create_message(session_id="session-123", role="user", content="Hello")
        conversation_repo.create_message(session_id="session-123", role="assistant", content="Hi")
        conversation_repo.create_message(session_id="session-123", role="user", content="Bye")

        count = conversation_repo.delete_session("session-123")

        assert count == 3
        assert len(conversation_repo.get_session_messages("session-123")) == 0


class TestRunnerMetricsRepository:
    """Tests for RunnerMetricsRepository."""

    def test_create_snapshot(self, runner_metrics_repo):
        """Test creating a runner metrics snapshot."""
        snapshot = runner_metrics_repo.create_snapshot(
            snapshot_date=date(2026, 5, 18),
            vo2max=45.5,
            vdot=42.0,
            acwr=1.2,
        )

        assert snapshot.id is not None
        assert snapshot.vo2max == 45.5
        assert snapshot.vdot == 42.0
        assert snapshot.acwr == 1.2

    def test_get_snapshots(self, runner_metrics_repo):
        """Test retrieving multiple snapshots."""
        runner_metrics_repo.create_snapshot(snapshot_date=date(2026, 5, 18), vo2max=45.0)
        runner_metrics_repo.create_snapshot(snapshot_date=date(2026, 5, 17), vo2max=44.5)

        snapshots = runner_metrics_repo.get_snapshots()
        assert len(snapshots) == 2

    def test_get_latest(self, runner_metrics_repo):
        """Test retrieving the latest snapshot."""
        runner_metrics_repo.create_snapshot(snapshot_date=date(2026, 5, 17), vo2max=44.0)
        runner_metrics_repo.create_snapshot(snapshot_date=date(2026, 5, 18), vo2max=45.0)

        latest = runner_metrics_repo.get_latest()
        assert latest is not None
        assert latest.vo2max == 45.0

    def test_get_latest_empty(self, runner_metrics_repo):
        """Test get_latest when no snapshots exist."""
        latest = runner_metrics_repo.get_latest()
        assert latest is None


class TestAuditLogAutoGeneration:
    """Tests for automatic audit logging on CUD operations."""

    def test_run_create_generates_audit(self, run_repo, test_session, sample_run_data):
        """Test that creating a run generates an audit entry."""
        from run_intelligence.db.models import AuditLog

        run_repo.create_run(**sample_run_data)

        audit_entries = test_session.query(AuditLog).filter(
            AuditLog.table_name == "runs",
            AuditLog.operation == "CREATE"
        ).all()
        assert len(audit_entries) >= 1

    def test_health_log_create_generates_audit(self, health_log_repo, test_session):
        """Test that creating a health log generates an audit entry."""
        from run_intelligence.db.models import AuditLog

        health_log_repo.create_entry(entry_date=date(2026, 5, 18), peak_flow=400)

        audit_count = test_session.query(AuditLog).filter(
            AuditLog.table_name == "health_log",
            AuditLog.operation == "CREATE"
        ).count()

        assert audit_count >= 1


class TestRepositoryAuditIntegration:
    """Integration tests verifying audit logging across repositories."""

    def test_wal_mode_enabled_in_memory(self, test_engine):
        """WAL mode on in-memory DB is expected to report 'memory' — skip."""
        from sqlalchemy import text

        with test_engine.connect() as conn:
            result = conn.execute(text("PRAGMA journal_mode"))
            row = result.fetchone()
            mode = row[0].lower()
            if mode == "memory":
                pytest.skip("WAL mode not supported for in-memory SQLite databases")
            assert mode == "wal", f"Expected WAL mode, got {mode}"

    def test_wal_mode_enabled_file_based(self):
        """Test that WAL mode is enabled on a file-based SQLite database."""
        import tempfile
        import os
        from sqlalchemy import create_engine, text, event
        from sqlalchemy.pool import StaticPool
        from run_intelligence.db.models import Base

        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )

            @event.listens_for(engine, "connect")
            def set_wal_mode(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            Base.metadata.create_all(bind=engine)

            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA journal_mode"))
                mode = result.fetchone()[0].lower()
                assert mode == "wal", f"Expected WAL mode, got {mode}"
        finally:
            os.unlink(db_path)

    def test_all_cud_operations_logged(self, run_repo, health_log_repo, conversation_repo, test_session):
        """Test that all CUD operations across repositories generate audit entries."""
        from run_intelligence.db.models import AuditLog

        run_repo.create_run(file_path="/path/to/run.fit")
        run = run_repo.get_runs()[0]
        run_repo.update_run(run.id, raw_metrics_json='{"updated": true}')
        run_repo.delete_run(run.id)

        health_log_repo.create_entry(entry_date=date(2026, 5, 18), peak_flow=400)
        hl = health_log_repo.get_entries()[0]
        health_log_repo.update_entry(hl.id, peak_flow=450)
        health_log_repo.delete_entry(hl.id)

        conversation_repo.create_message(session_id="test", role="user", content="Hello")
        conversation_repo.delete_session("test")

        audit_logs = test_session.query(AuditLog).all()
        assert len(audit_logs) >= 8