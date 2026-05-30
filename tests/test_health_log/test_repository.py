"""Unit tests for HealthLogRepository."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, call

import pytest

from run_intelligence.db.models import HealthLog, AuditLog


class TestHealthLogRepositoryCreate:
    """Tests for create_entry method."""

    def test_create_entry_with_all_fields(self, health_log_repo, test_session):
        """Test creating a health log entry with all fields."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
            sleep_quality=4,
            post_run_rpe=7,
            asthma_symptoms=2,
            saba_use=True,
            notes="Test notes",
        )

        assert entry.id is not None
        assert entry.date == date(2026, 5, 21)
        assert entry.peak_flow == 450
        assert entry.sleep_quality == 4
        assert entry.post_run_rpe == 7
        assert entry.asthma_symptoms == 2
        assert entry.saba_use is True
        assert entry.notes == "Test notes"

    def test_create_entry_minimal_fields(self, health_log_repo, test_session):
        """Test creating a health log entry with only required fields."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
        )

        assert entry.id is not None
        assert entry.date == date(2026, 5, 21)
        assert entry.peak_flow is None
        assert entry.sleep_quality is None
        assert entry.saba_use is None

    def test_create_entry_defaults_to_today(self, health_log_repo, test_session):
        """Test that entry date defaults to today when not provided."""
        entry = health_log_repo.create_entry()

        assert entry.date == date.today()

    def test_create_entry_optional_fields_can_be_none(self, health_log_repo, test_session):
        """Test that optional fields can be None."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=None,
            sleep_quality=None,
            saba_use=None,
            notes=None,
        )

        assert entry.peak_flow is None
        assert entry.sleep_quality is None
        assert entry.saba_use is None
        assert entry.notes is None

    def test_create_entry_audit_log_created(self, health_log_repo, test_session):
        """Test that an audit log entry is created on create."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )

        # Check audit log was created
        audit_logs = test_session.query(AuditLog).filter(
            AuditLog.table_name == "health_log",
            AuditLog.operation == "CREATE",
            AuditLog.record_id == entry.id,
        ).all()

        assert len(audit_logs) == 1
        assert audit_logs[0].agent == "health_log"


class TestHealthLogRepositoryRead:
    """Tests for get_entry and get_entries methods."""

    def test_get_entry_exists(self, health_log_repo, test_session):
        """Test getting an existing entry by ID."""
        # Create an entry first
        created = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )

        # Get it back
        retrieved = health_log_repo.get_entry(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.date == date(2026, 5, 21)
        assert retrieved.peak_flow == 450

    def test_get_entry_not_exists(self, health_log_repo, test_session):
        """Test getting a non-existent entry returns None."""
        result = health_log_repo.get_entry(99999)
        assert result is None

    def test_get_entries_returns_all(self, health_log_repo, test_session):
        """Test getting all entries."""
        # Create multiple entries
        health_log_repo.create_entry(entry_date=date(2026, 5, 21), peak_flow=450)
        health_log_repo.create_entry(entry_date=date(2026, 5, 22), peak_flow=460)
        health_log_repo.create_entry(entry_date=date(2026, 5, 23), peak_flow=470)

        entries = health_log_repo.get_entries()

        assert len(entries) == 3

    def test_get_entries_respects_limit(self, health_log_repo, test_session):
        """Test that get_entries respects the limit parameter."""
        # Create more than limit entries
        for i in range(5):
            health_log_repo.create_entry(
                entry_date=date(2026, 5, 20 + i),
                peak_flow=400 + i * 10,
            )

        entries = health_log_repo.get_entries(limit=3)

        assert len(entries) == 3

    def test_get_entries_ordered_by_date_desc(self, health_log_repo, test_session):
        """Test entries are ordered by date descending."""
        health_log_repo.create_entry(entry_date=date(2026, 5, 21), peak_flow=450)
        health_log_repo.create_entry(entry_date=date(2026, 5, 23), peak_flow=470)
        health_log_repo.create_entry(entry_date=date(2026, 5, 22), peak_flow=460)

        entries = health_log_repo.get_entries()

        # Should be ordered by date descending (most recent first)
        assert entries[0].date == date(2026, 5, 23)
        assert entries[1].date == date(2026, 5, 22)
        assert entries[2].date == date(2026, 5, 21)


class TestHealthLogRepositoryUpdate:
    """Tests for update_entry method."""

    def test_update_entry_single_field(self, health_log_repo, test_session):
        """Test updating a single field."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )

        updated = health_log_repo.update_entry(
            entry_id=entry.id,
            peak_flow=460,
        )

        assert updated is not None
        assert updated.peak_flow == 460
        # Other fields unchanged
        assert updated.date == date(2026, 5, 21)

    def test_update_entry_multiple_fields(self, health_log_repo, test_session):
        """Test updating multiple fields."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
            sleep_quality=3,
        )

        updated = health_log_repo.update_entry(
            entry_id=entry.id,
            peak_flow=460,
            sleep_quality=4,
            saba_use=True,
        )

        assert updated.peak_flow == 460
        assert updated.sleep_quality == 4
        assert updated.saba_use is True

    def test_update_entry_not_exists(self, health_log_repo, test_session):
        """Test updating non-existent entry returns None."""
        result = health_log_repo.update_entry(
            entry_id=99999,
            peak_flow=500,
        )

        assert result is None

    def test_update_entry_audit_log_created(self, health_log_repo, test_session):
        """Test that an audit log entry is created on update."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )

        health_log_repo.update_entry(
            entry_id=entry.id,
            peak_flow=460,
        )

        # Check audit log was created
        audit_logs = test_session.query(AuditLog).filter(
            AuditLog.table_name == "health_log",
            AuditLog.operation == "UPDATE",
            AuditLog.record_id == entry.id,
        ).all()

        assert len(audit_logs) == 1


class TestHealthLogRepositoryDelete:
    """Tests for delete_entry method."""

    def test_delete_entry_exists(self, health_log_repo, test_session):
        """Test deleting an existing entry."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )
        entry_id = entry.id

        result = health_log_repo.delete_entry(entry_id)

        assert result is True

        # Verify it's gone
        assert health_log_repo.get_entry(entry_id) is None

    def test_delete_entry_not_exists(self, health_log_repo, test_session):
        """Test deleting non-existent entry returns False."""
        result = health_log_repo.delete_entry(99999)
        assert result is False

    def test_delete_entry_audit_log_created(self, health_log_repo, test_session):
        """Test that an audit log entry is created on delete."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )

        health_log_repo.delete_entry(entry.id)

        # Check audit log was created
        audit_logs = test_session.query(AuditLog).filter(
            AuditLog.table_name == "health_log",
            AuditLog.operation == "DELETE",
            AuditLog.record_id == entry.id,
        ).all()

        assert len(audit_logs) == 1


class TestHealthLogRepositoryLinkToRun:
    """Tests for link_to_run method."""

    def test_link_to_run_success(self, health_log_repo, run_repo, test_session):
        """Test linking a health log entry to a run."""
        # Create a run
        run = run_repo.create_run(file_path="/test/run.fit")

        # Create a health log entry
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )

        # Link them
        linked = health_log_repo.link_to_run(entry.id, run.id)

        assert linked is not None
        assert linked.run_id == run.id

    def test_link_to_run_invalid_entry(self, health_log_repo, run_repo, test_session):
        """Test linking with invalid entry ID returns None."""
        run = run_repo.create_run(file_path="/test/run.fit")

        result = health_log_repo.link_to_run(99999, run.id)

        assert result is None

    def test_link_to_run_invalid_run(self, health_log_repo, test_session):
        """Test linking with invalid run ID returns None."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
        )

        result = health_log_repo.link_to_run(entry.id, 99999)

        assert result is None


class TestHealthLogRepositoryEdgeCases:
    """Edge case tests for HealthLogRepository."""

    def test_create_entry_with_run_id(self, health_log_repo, run_repo, test_session):
        """Test creating entry with a run ID."""
        run = run_repo.create_run(file_path="/test/run.fit")

        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            peak_flow=450,
            run_id=run.id,
        )

        assert entry.run_id == run.id

    def test_update_notes_field(self, health_log_repo, test_session):
        """Test updating the notes field."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            notes="Original notes",
        )

        updated = health_log_repo.update_entry(
            entry_id=entry.id,
            notes="Updated notes",
        )

        assert updated.notes == "Updated notes"

    def test_update_saba_use_field(self, health_log_repo, test_session):
        """Test updating the saba_use boolean field."""
        entry = health_log_repo.create_entry(
            entry_date=date(2026, 5, 21),
            saba_use=False,
        )

        updated = health_log_repo.update_entry(
            entry_id=entry.id,
            saba_use=True,
        )

        assert updated.saba_use is True

    def test_get_entries_limit_invalid_uses_default(self, health_log_repo, test_session):
        """Test that invalid limit uses default."""
        # Create some entries
        health_log_repo.create_entry(entry_date=date(2026, 5, 21), peak_flow=450)

        # Use invalid limit (0 or negative)
        entries = health_log_repo.get_entries(limit=0)
        
        # Should return results (implementation uses default of 100)
        assert len(entries) >= 1
