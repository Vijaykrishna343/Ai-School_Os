"""
BackgroundJob Repository — Database access layer for asynchronous tasks.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.background_job import BackgroundJob, JobStatus, JobType


class JobRepository:
    def create_job(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        job_type: JobType,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
        max_retries: int = 3,
        total_items: int = 0,
    ) -> BackgroundJob:
        if idempotency_key:
            existing = self.get_by_idempotency_key(db, school_id, idempotency_key)
            if existing:
                return existing

        job = BackgroundJob(
            school_id=school_id,
            created_by_user_id=user_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            payload=payload,
            idempotency_key=idempotency_key,
            max_retries=max_retries,
            total_items=total_items,
        )
        db.add(job)
        db.flush()
        return job

    def get_by_id(self, db: Session, school_id: UUID, job_id: UUID) -> BackgroundJob | None:
        return db.scalar(
            select(BackgroundJob).where(
                BackgroundJob.id == job_id,
                BackgroundJob.school_id == school_id,
                BackgroundJob.is_deleted.is_(False),
            )
        )

    def get_by_idempotency_key(self, db: Session, school_id: UUID, idempotency_key: str) -> BackgroundJob | None:
        return db.scalar(
            select(BackgroundJob).where(
                BackgroundJob.idempotency_key == idempotency_key,
                BackgroundJob.school_id == school_id,
                BackgroundJob.is_deleted.is_(False),
            )
        )

    def update_progress(
        self,
        db: Session,
        job: BackgroundJob,
        processed_items: int,
        total_items: int | None = None,
    ) -> BackgroundJob:
        if total_items is not None:
            job.total_items = total_items
        job.processed_items = processed_items
        if job.total_items > 0:
            job.progress_percentage = min(100, int((processed_items / job.total_items) * 100))
        db.flush()
        return job

    def mark_started(self, db: Session, job: BackgroundJob) -> BackgroundJob:
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        db.flush()
        return job

    def mark_completed(self, db: Session, job: BackgroundJob, result: dict[str, Any] | None = None) -> BackgroundJob:
        job.status = JobStatus.COMPLETED
        job.progress_percentage = 100
        job.result = result
        job.completed_at = datetime.now(timezone.utc)
        db.flush()
        return job

    def mark_failed(self, db: Session, job: BackgroundJob, error_message: str) -> BackgroundJob:
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        db.flush()
        return job

    def mark_cancelled(self, db: Session, job: BackgroundJob) -> BackgroundJob:
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        db.flush()
        return job

    def recover_orphaned_jobs(self, db: Session) -> int:
        """
        Recovers jobs left in PROCESSING state due to application restart or worker crash.
        Resets retryable jobs to QUEUED; marks non-retryable jobs as FAILED.
        """
        orphans = db.scalars(
            select(BackgroundJob).where(
                BackgroundJob.status == JobStatus.PROCESSING,
                BackgroundJob.is_deleted.is_(False),
            )
        ).all()

        recovered_count = 0
        now = datetime.now(timezone.utc)
        for job in orphans:
            job.retry_count += 1
            if job.retry_count <= job.max_retries:
                job.status = JobStatus.QUEUED
                job.started_at = None
                job.error_message = f"Job interrupted by process restart (Retry {job.retry_count}/{job.max_retries})"
            else:
                job.status = JobStatus.FAILED
                job.completed_at = now
                job.error_message = f"Job interrupted by process restart and exceeded max retries ({job.max_retries})"
            recovered_count += 1

        if recovered_count > 0:
            db.commit()

        return recovered_count


job_repository = JobRepository()

