"""
BackgroundJob model definition for Phase 2 Workstream 3 — Async Background Processing & Notification Queue.
"""
from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.common_model import CommonModel


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(str, enum.Enum):
    BATCH_REPORT_CARD_GEN = "BATCH_REPORT_CARD_GEN"
    BULK_NOTIFICATION_DISPATCH = "BULK_NOTIFICATION_DISPATCH"
    BULK_STUDENT_IMPORT = "BULK_STUDENT_IMPORT"


class BackgroundJob(CommonModel):
    """
    Represents an asynchronous background processing task.
    Enforces multi-tenant isolation via school_id.
    """
    __tablename__ = "background_jobs"

    __table_args__ = (
        Index("ix_background_jobs_school_id", "school_id"),
        Index("ix_background_jobs_status", "status"),
        Index("ix_background_jobs_type", "job_type"),
        Index("ix_background_jobs_idempotency", "idempotency_key", unique=True),
    )

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    job_type: Mapped[JobType] = mapped_column(
        SQLEnum(JobType, native_enum=False, create_type=False),
        nullable=False,
    )

    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, native_enum=False, create_type=False),
        default=JobStatus.QUEUED,
        nullable=False,
    )

    progress_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    processed_items: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    total_items: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
