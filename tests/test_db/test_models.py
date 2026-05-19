"""Tests for SQLAlchemy database models."""

import json
from datetime import date

from run_intelligence.db.models import Run, HealthLog, ConversationHistory, RunnerMetricsHistory, AuditLog


class TestRunModel:
    """Tests for the Run model."""

    def test_run_creation(self, test_session):
        """Test creating a Run instance."""
        run = Run(
            file_path="/path/to/test.fit",
            raw_metrics_json='{"pace": 5.5}',
            derived_metrics_json='{"vo2max": 45.0}',
            data_quality_flags_json='{}',
        )
        test_session.add(run)
        test_session.flush()

        assert run.id is not None
        assert run.file_path == "/path/to/test.fit"
        assert run.raw_metrics_json == '{"pace": 5.5}'
        assert run.derived_metrics_json == '{"vo2max": 45.0}'
        assert run.data_quality_flags_json == '{}'
        assert run.processed_at is not None

    def test_run_repr(self, test_session):
        """Test Run __repr__ method."""
        run = Run(file_path="/path/to/test.fit")
        test_session.add(run)
        test_session.flush()

        repr_str = repr(run)
        assert "Run" in repr_str
        assert "test.fit" in repr_str


class TestHealthLogModel:
    """Tests for the HealthLog model."""

    def test_health_log_creation(self, test_session):
        """Test creating a HealthLog instance."""
        health_log = HealthLog(
            date=date(2026, 5, 18),
            peak_flow=450,
            sleep_quality=3,
            post_run_rpe=12,
            asthma_symptoms=1,
            saba_use=False,
            notes="Test note",
        )
        test_session.add(health_log)
        test_session.flush()

        assert health_log.id is not None
        assert health_log.date == date(2026, 5, 18)
        assert health_log.peak_flow == 450
        assert health_log.sleep_quality == 3
        assert health_log.post_run_rpe == 12
        assert health_log.asthma_symptoms == 1
        assert health_log.saba_use is False
        assert health_log.notes == "Test note"
        assert health_log.run_id is None

    def test_health_log_nullable_fields(self, test_session):
        """Test HealthLog with only required fields."""
        health_log = HealthLog(date=date(2026, 5, 18))
        test_session.add(health_log)
        test_session.flush()

        assert health_log.id is not None
        assert health_log.date == date(2026, 5, 18)
        assert health_log.peak_flow is None

    def test_health_log_repr(self, test_session):
        """Test HealthLog __repr__ method."""
        health_log = HealthLog(date=date(2026, 5, 18), peak_flow=450)
        test_session.add(health_log)
        test_session.flush()

        repr_str = repr(health_log)
        assert "HealthLog" in repr_str
        assert "450" in repr_str


class TestConversationHistoryModel:
    """Tests for the ConversationHistory model."""

    def test_conversation_history_creation(self, test_session):
        """Test creating a ConversationHistory instance."""
        message = ConversationHistory(
            session_id="session-123",
            role="user",
            content="Hello, world!",
        )
        test_session.add(message)
        test_session.flush()

        assert message.id is not None
        assert message.session_id == "session-123"
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.created_at is not None

    def test_conversation_history_repr(self, test_session):
        """Test ConversationHistory __repr__ method."""
        message = ConversationHistory(
            session_id="session-123",
            role="assistant",
            content="Hi there!",
        )
        test_session.add(message)
        test_session.flush()

        repr_str = repr(message)
        assert "ConversationHistory" in repr_str
        assert "session-123" in repr_str


class TestRunnerMetricsHistoryModel:
    """Tests for the RunnerMetricsHistory model."""

    def test_runner_metrics_creation(self, test_session):
        """Test creating a RunnerMetricsHistory instance."""
        metrics = RunnerMetricsHistory(
            date=date(2026, 5, 18),
            vo2max=45.5,
            vdot=42.0,
            acwr=1.2,
        )
        test_session.add(metrics)
        test_session.flush()

        assert metrics.id is not None
        assert metrics.date == date(2026, 5, 18)
        assert metrics.vo2max == 45.5
        assert metrics.vdot == 42.0
        assert metrics.acwr == 1.2
        assert metrics.source_run_id is None

    def test_runner_metrics_repr(self, test_session):
        """Test RunnerMetricsHistory __repr__ method."""
        metrics = RunnerMetricsHistory(date=date(2026, 5, 18), vo2max=45.5)
        test_session.add(metrics)
        test_session.flush()

        repr_str = repr(metrics)
        assert "RunnerMetricsHistory" in repr_str
        assert "45.5" in repr_str


class TestAuditLogModel:
    """Tests for the AuditLog model."""

    def test_audit_log_creation(self, test_session):
        """Test creating an AuditLog instance."""
        audit = AuditLog(
            operation="CREATE",
            table_name="runs",
            agent="pipeline",
            record_id=1,
            details='{"key": "value"}',
        )
        test_session.add(audit)
        test_session.flush()

        assert audit.id is not None
        assert audit.operation == "CREATE"
        assert audit.table_name == "runs"
        assert audit.agent == "pipeline"
        assert audit.record_id == 1
        assert audit.details == '{"key": "value"}'
        assert audit.timestamp is not None

    def test_audit_log_repr(self, test_session):
        """Test AuditLog __repr__ method."""
        audit = AuditLog(operation="UPDATE", table_name="health_log", agent="health_log")
        test_session.add(audit)
        test_session.flush()

        repr_str = repr(audit)
        assert "AuditLog" in repr_str
        assert "UPDATE" in repr_str


class TestJsonSerializationRoundTrip:
    """Test JSON serialization and deserialization round-trip."""

    def test_run_json_roundtrip(self, test_session):
        """Test Run JSON fields survive a session commit and reload."""
        original_data = {
            "raw_metrics": {"pace": 5.5, "hr": 145},
            "derived_metrics": {"vo2max": 45.2, "vdot": 42.1},
            "quality_flags": {"hr_artifacts": False, "gps_drift": 0.02},
        }

        run = Run(
            file_path="/path/to/test.fit",
            raw_metrics_json=json.dumps(original_data["raw_metrics"]),
            derived_metrics_json=json.dumps(original_data["derived_metrics"]),
            data_quality_flags_json=json.dumps(original_data["quality_flags"]),
        )
        test_session.add(run)
        test_session.commit()

        reloaded = test_session.query(Run).filter(Run.id == run.id).first()
        assert json.loads(reloaded.raw_metrics_json) == original_data["raw_metrics"]
        assert json.loads(reloaded.derived_metrics_json) == original_data["derived_metrics"]
        assert json.loads(reloaded.data_quality_flags_json) == original_data["quality_flags"]