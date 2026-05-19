"""SQLAlchemy declarative models for all database tables."""

from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class Run(Base):
    """Model for processed .fit file runs."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    raw_metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    derived_metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_quality_flags_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    health_logs: Mapped[list["HealthLog"]] = relationship("HealthLog", back_populates="run")
    runner_metrics: Mapped[list["RunnerMetricsHistory"]] = relationship("RunnerMetricsHistory", back_populates="source_run")

    def __repr__(self) -> str:
        return f"<Run(id={self.id}, file_path='{self.file_path}', processed_at={self.processed_at})>"


class HealthLog(Base):
    """Model for health log entries."""

    __tablename__ = "health_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    peak_flow: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_quality: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    post_run_rpe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    asthma_symptoms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    saba_use: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("runs.id"), nullable=True)

    run: Mapped[Optional["Run"]] = relationship("Run", back_populates="health_logs")

    def __repr__(self) -> str:
        return f"<HealthLog(id={self.id}, date={self.date}, peak_flow={self.peak_flow})>"


class ConversationHistory(Base):
    """Model for conversation history messages."""

    __tablename__ = "conversation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<ConversationHistory(id={self.id}, session_id='{self.session_id}', role='{self.role}')>"


class RunnerMetricsHistory(Base):
    """Model for runner metrics history snapshots."""

    __tablename__ = "runner_metrics_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    vo2max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vdot: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    acwr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_run_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("runs.id"), nullable=True)

    source_run: Mapped[Optional["Run"]] = relationship("Run", back_populates="runner_metrics")

    def __repr__(self) -> str:
        return f"<RunnerMetricsHistory(id={self.id}, date={self.date}, vo2max={self.vo2max})>"


class AuditLog(Base):
    """Model for audit log entries tracking data operations."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    operation: Mapped[str] = mapped_column(String(32), nullable=False)
    table_name: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    agent: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, timestamp={self.timestamp}, operation='{self.operation}', agent='{self.agent}')>"