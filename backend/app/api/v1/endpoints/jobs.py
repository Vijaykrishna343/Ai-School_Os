"""
Background Jobs API Endpoints — Phase 2 Workstream 3.
Provides HTTP routes for polling background job status, retrying, and cancelling tasks.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.authorization import enforce_relationship_access
from app.common.exceptions import NotFoundException
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.background_job import JobStatus
from app.repositories.job_repository import job_repository
from app.schemas.background_job import BackgroundJobResponse
from app.services.async_job_runner import async_job_runner

router = APIRouter()


@router.get("/{job_id}", response_model=dict, summary="Get Job Status")
def get_job_status(
    job_id: UUID,
    current_user: IdentityUser = Depends(require_permission("school.view")),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Retrieve background job status and progress.
    Enforces tenant isolation and relationship security.
    """
    enforce_relationship_access(db, current_user.school_id, current_user)

    job = job_repository.get_by_id(db, current_user.school_id, job_id)
    if not job:
        raise NotFoundException(f"Job '{job_id}' not found.")

    res = BackgroundJobResponse.model_validate(job).model_dump(mode="json")
    return JSONResponse(content={"success": True, "data": res})


@router.post("/{job_id}/retry", response_model=dict, summary="Retry Failed Job")
def retry_job(
    job_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: IdentityUser = Depends(require_permission("school.update")),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Re-queue a failed job for execution.
    """
    enforce_relationship_access(db, current_user.school_id, current_user)

    job = job_repository.get_by_id(db, current_user.school_id, job_id)
    if not job:
        raise NotFoundException(f"Job '{job_id}' not found.")

    if job.retry_count >= job.max_retries:
        from app.common.exceptions import BadRequestException
        raise BadRequestException(f"Job '{job_id}' has reached its maximum retry limit ({job.max_retries}).")

    job.status = JobStatus.QUEUED
    job.retry_count += 1
    job.error_message = None
    db.commit()

    background_tasks.add_task(async_job_runner.process_job, current_user.school_id, job.id)

    res = BackgroundJobResponse.model_validate(job).model_dump(mode="json")
    return JSONResponse(content={"success": True, "data": res})


@router.post("/{job_id}/cancel", response_model=dict, summary="Cancel Job")
def cancel_job(
    job_id: UUID,
    current_user: IdentityUser = Depends(require_permission("school.update")),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Mark a queued or processing job as cancelled.
    """
    enforce_relationship_access(db, current_user.school_id, current_user)

    job = job_repository.get_by_id(db, current_user.school_id, job_id)
    if not job:
        raise NotFoundException(f"Job '{job_id}' not found.")

    job_repository.mark_cancelled(db, job)
    db.commit()

    res = BackgroundJobResponse.model_validate(job).model_dump(mode="json")
    return JSONResponse(content={"success": True, "data": res})
