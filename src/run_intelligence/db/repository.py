"""Repository layer for CRUD operations on all database entities."""

from datetime import date, datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session, sessionmaker

from run_intelligence.db.models import (
    Run,
    HealthLog,
    ConversationHistory,
    RunnerMetricsHistory,
    AuditLog,
)

_UNSET = object()
_VALID_OPERATIONS = {"CREATE", "READ", "UPDATE", "DELETE"}
_VALID_ROLES = {"user", "assistant"}


def _ensure_positive_limit(limit: int, default: int) -> int:
    """Ensure limit is a positive integer."""
    if not isinstance(limit, int) or limit < 1:
        return default
    return limit


class AuditLogRepository:
    """Repository for audit log operations."""

    def __init__(self, session: Session, engine=None):
        self.session = session
        self._engine = engine

    def log_operation(
        self,
        operation: str,
        table_name: str,
        agent: str,
        record_id: Optional[int] = None,
        details: Optional[str] = None,
    ) -> AuditLog:
        """Log an operation to the audit trail."""
        if operation not in _VALID_OPERATIONS:
            raise ValueError(f"Invalid audit operation: {operation!r}")

        audit_entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            operation=operation,
            table_name=table_name,
            record_id=record_id,
            agent=agent,
            details=details,
        )

        if self._engine is not None:
            # Use a separate session so audit survives caller rollback
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            audit_session = SessionLocal()
            try:
                audit_session.add(audit_entry)
                audit_session.commit()
                return audit_entry
            finally:
                audit_session.close()
        else:
            # Fallback: use the shared session (test / backward compat)
            self.session.add(audit_entry)
            self.session.flush()
            return audit_entry


class RunRepository:
    """Repository for Run entity CRUD operations."""

    def __init__(self, session: Session, audit_logger: AuditLogRepository):
        self.session = session
        self.audit_logger = audit_logger

    def create_run(
        self,
        file_path: str,
        raw_metrics_json: Optional[str] = None,
        derived_metrics_json: Optional[str] = None,
        data_quality_flags_json: Optional[str] = None,
    ) -> Run:
        """Create a new run record."""
        run = Run(
            file_path=file_path,
            raw_metrics_json=raw_metrics_json,
            derived_metrics_json=derived_metrics_json,
            data_quality_flags_json=data_quality_flags_json,
        )
        self.session.add(run)
        self.session.flush()
        self.audit_logger.log_operation(
            operation="CREATE",
            table_name="runs",
            agent="pipeline",
            record_id=run.id,
        )
        self.session.commit()
        return run

    def get_run(self, run_id: int) -> Optional[Run]:
        """Get a run by ID."""
        return self.session.query(Run).filter(Run.id == run_id).first()

    def get_runs(self, limit: int = 100) -> List[Run]:
        """Get all runs with optional limit."""
        limit = _ensure_positive_limit(limit, 100)
        return self.session.query(Run).order_by(Run.processed_at.desc()).limit(limit).all()

    def update_run(
        self,
        run_id: int,
        raw_metrics_json: Optional[str] = _UNSET,
        derived_metrics_json: Optional[str] = _UNSET,
        data_quality_flags_json: Optional[str] = _UNSET,
    ) -> Optional[Run]:
        """Update an existing run."""
        run = self.get_run(run_id)
        if not run:
            return None
        if raw_metrics_json is not _UNSET:
            run.raw_metrics_json = raw_metrics_json
        if derived_metrics_json is not _UNSET:
            run.derived_metrics_json = derived_metrics_json
        if data_quality_flags_json is not _UNSET:
            run.data_quality_flags_json = data_quality_flags_json
        self.session.flush()
        self.audit_logger.log_operation(
            operation="UPDATE",
            table_name="runs",
            agent="pipeline",
            record_id=run.id,
        )
        self.session.commit()
        return run

    def delete_run(self, run_id: int) -> bool:
        """Delete a run by ID."""
        run = self.get_run(run_id)
        if not run:
            return False
        self.session.delete(run)
        self.session.flush()
        self.audit_logger.log_operation(
            operation="DELETE",
            table_name="runs",
            agent="pipeline",
            record_id=run_id,
        )
        self.session.commit()
        return True


class HealthLogRepository:
    """Repository for HealthLog entity CRUD operations."""

    def __init__(self, session: Session, audit_logger: AuditLogRepository):
        self.session = session
        self.audit_logger = audit_logger

    def create_entry(
        self,
        entry_date: Optional[date] = None,
        peak_flow: Optional[int] = None,
        sleep_quality: Optional[int] = None,
        post_run_rpe: Optional[int] = None,
        asthma_symptoms: Optional[int] = None,
        saba_use: Optional[bool] = None,
        notes: Optional[str] = None,
        run_id: Optional[int] = None,
    ) -> HealthLog:
        """Create a new health log entry."""
        if entry_date is None:
            entry_date = date.today()
        health_log = HealthLog(
            date=entry_date,
            peak_flow=peak_flow,
            sleep_quality=sleep_quality,
            post_run_rpe=post_run_rpe,
            asthma_symptoms=asthma_symptoms,
            saba_use=saba_use,
            notes=notes,
            run_id=run_id,
        )
        self.session.add(health_log)
        self.session.flush()
        self.audit_logger.log_operation(
            operation="CREATE",
            table_name="health_log",
            agent="health_log",
            record_id=health_log.id,
        )
        self.session.commit()
        return health_log

    def get_entry(self, entry_id: int) -> Optional[HealthLog]:
        """Get a health log entry by ID."""
        return self.session.query(HealthLog).filter(HealthLog.id == entry_id).first()

    def get_entries(self, limit: int = 100) -> List[HealthLog]:
        """Get all health log entries with optional limit."""
        limit = _ensure_positive_limit(limit, 100)
        return self.session.query(HealthLog).order_by(HealthLog.date.desc()).limit(limit).all()

    def update_entry(
        self,
        entry_id: int,
        peak_flow: Optional[int] = _UNSET,
        sleep_quality: Optional[int] = _UNSET,
        post_run_rpe: Optional[int] = _UNSET,
        asthma_symptoms: Optional[int] = _UNSET,
        saba_use: Optional[bool] = _UNSET,
        notes: Optional[str] = _UNSET,
        run_id: Optional[int] = _UNSET,
    ) -> Optional[HealthLog]:
        """Update an existing health log entry."""
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        if peak_flow is not _UNSET:
            entry.peak_flow = peak_flow
        if sleep_quality is not _UNSET:
            entry.sleep_quality = sleep_quality
        if post_run_rpe is not _UNSET:
            entry.post_run_rpe = post_run_rpe
        if asthma_symptoms is not _UNSET:
            entry.asthma_symptoms = asthma_symptoms
        if saba_use is not _UNSET:
            entry.saba_use = saba_use
        if notes is not _UNSET:
            entry.notes = notes
        if run_id is not _UNSET:
            entry.run_id = run_id
        self.session.flush()
        self.audit_logger.log_operation(
            operation="UPDATE",
            table_name="health_log",
            agent="health_log",
            record_id=entry.id,
        )
        self.session.commit()
        return entry

    def delete_entry(self, entry_id: int) -> bool:
        """Delete a health log entry by ID."""
        entry = self.get_entry(entry_id)
        if not entry:
            return False
        self.session.delete(entry)
        self.session.flush()
        self.audit_logger.log_operation(
            operation="DELETE",
            table_name="health_log",
            agent="health_log",
            record_id=entry_id,
        )
        self.session.commit()
        return True

    def link_to_run(self, entry_id: int, run_id: int) -> Optional[HealthLog]:
        """Link a health log entry to a run."""
        run = self.session.query(Run).filter(Run.id == run_id).first()
        if not run:
            return None
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        entry.run_id = run_id
        self.session.flush()
        self.audit_logger.log_operation(
            operation="UPDATE",
            table_name="health_log",
            agent="health_log",
            record_id=entry_id,
            details=f"Linked to run_id={run_id}",
        )
        self.session.commit()
        return entry


class ConversationRepository:
    """Repository for ConversationHistory entity CRUD operations."""

    def __init__(self, session: Session, audit_logger: AuditLogRepository):
        self.session = session
        self.audit_logger = audit_logger

    def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> ConversationHistory:
        """Create a new conversation message."""
        if role not in _VALID_ROLES:
            raise ValueError(f"Invalid conversation role: {role!r}")

        message = ConversationHistory(
            session_id=session_id,
            role=role,
            content=content,
        )
        self.session.add(message)
        self.session.flush()
        self.audit_logger.log_operation(
            operation="CREATE",
            table_name="conversation_history",
            agent="coach",
            record_id=message.id,
        )
        self.session.commit()
        return message

    def get_session_messages(self, session_id: str, limit: int = 1000) -> List[ConversationHistory]:
        """Get all messages for a conversation session."""
        limit = _ensure_positive_limit(limit, 1000)
        return (
            self.session.query(ConversationHistory)
            .filter(ConversationHistory.session_id == session_id)
            .order_by(ConversationHistory.created_at)
            .limit(limit)
            .all()
        )

    def delete_session(self, session_id: str) -> int:
        """Delete all messages for a session. Returns count of deleted messages."""
        count = (
            self.session.query(ConversationHistory)
            .filter(ConversationHistory.session_id == session_id)
            .delete()
        )
        self.session.flush()
        self.audit_logger.log_operation(
            operation="DELETE",
            table_name="conversation_history",
            agent="coach",
            details=f"Deleted session {session_id} with {count} messages",
        )
        self.session.commit()
        return count


class RunnerMetricsRepository:
    """Repository for RunnerMetricsHistory entity CRUD operations."""

    def __init__(self, session: Session, audit_logger: AuditLogRepository):
        self.session = session
        self.audit_logger = audit_logger

    def create_snapshot(
        self,
        snapshot_date: date,
        vo2max: Optional[float] = None,
        vdot: Optional[float] = None,
        acwr: Optional[float] = None,
        source_run_id: Optional[int] = None,
    ) -> RunnerMetricsHistory:
        """Create a new runner metrics snapshot."""
        snapshot = RunnerMetricsHistory(
            date=snapshot_date,
            vo2max=vo2max,
            vdot=vdot,
            acwr=acwr,
            source_run_id=source_run_id,
        )
        self.session.add(snapshot)
        self.session.flush()
        self.audit_logger.log_operation(
            operation="CREATE",
            table_name="runner_metrics_history",
            agent="pipeline",
            record_id=snapshot.id,
        )
        self.session.commit()
        return snapshot

    def get_snapshots(self, limit: int = 30) -> List[RunnerMetricsHistory]:
        """Get runner metrics snapshots with optional limit."""
        limit = _ensure_positive_limit(limit, 30)
        return (
            self.session.query(RunnerMetricsHistory)
            .order_by(RunnerMetricsHistory.date.desc())
            .limit(limit)
            .all()
        )

    def get_latest(self) -> Optional[RunnerMetricsHistory]:
        """Get the most recent runner metrics snapshot."""
        return (
            self.session.query(RunnerMetricsHistory)
            .order_by(RunnerMetricsHistory.date.desc())
            .first()
        )
