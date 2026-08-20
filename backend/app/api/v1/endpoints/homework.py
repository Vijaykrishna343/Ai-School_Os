"""
Homework & Assignments API Endpoint Router.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.current_user import get_current_user
from app.models.homework.homework import HomeworkStatus
from app.schemas.homework.homework import (
    HomeworkCreate,
    HomeworkListResponse,
    HomeworkResponse,
    HomeworkSummaryResponse,
    HomeworkUpdate,
)
from app.schemas.homework.homework_submission import (
    HomeworkSubmissionCreate,
    HomeworkSubmissionGrade,
    HomeworkSubmissionListResponse,
    HomeworkSubmissionResponse,
)
from app.services.homework_service import homework_service

router = APIRouter()


def get_current_user_with_role(
    user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[IdentityUser, str]:
    user_role = db.scalar(
        select(IdentityUserRole).where(IdentityUserRole.user_id == user.id)
    )
    role_name = "Teacher"
    if user_role:
        role = db.get(IdentityRole, user_role.role_id)
        if role:
            role_name = role.name
    return user, role_name


@router.post(
    "",
    response_model=HomeworkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("homework.create"))],
)
def create_homework(
    payload: HomeworkCreate,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, _ = user_context
    return homework_service.create_homework(
        db=db,
        school_id=user.school_id,
        current_user=user,
        payload=payload,
    )


@router.get(
    "",
    response_model=HomeworkListResponse,
    dependencies=[Depends(require_permission("homework.view"))],
)
def list_homework(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    school_class_id: UUID | None = Query(None),
    section_id: UUID | None = Query(None),
    subject_id: UUID | None = Query(None),
    status: HomeworkStatus | None = Query(None),
    teacher_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    return homework_service.list_homework(
        db=db,
        school_id=user.school_id,
        current_user=user,
        user_role=role_name,
        page=page,
        page_size=page_size,
        school_class_id=school_class_id,
        section_id=section_id,
        subject_id=subject_id,
        status=status,
        teacher_id=teacher_id,
        student_id=student_id,
    )


@router.get(
    "/summary",
    response_model=HomeworkSummaryResponse,
    dependencies=[Depends(require_permission("homework.view"))],
)
def get_homework_summary(
    teacher_id: UUID | None = Query(None),
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, _ = user_context
    return homework_service.get_homework_summary(
        db=db,
        school_id=user.school_id,
        teacher_id=teacher_id,
    )


@router.get(
    "/{homework_id}",
    response_model=HomeworkResponse,
    dependencies=[Depends(require_permission("homework.view"))],
)
def get_homework(
    homework_id: UUID,
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return homework_service.get_homework_by_id(
        db=db,
        school_id=user.school_id,
        homework_id=homework_id,
    )


@router.put(
    "/{homework_id}",
    response_model=HomeworkResponse,
    dependencies=[Depends(require_permission("homework.update"))],
)
def update_homework(
    homework_id: UUID,
    payload: HomeworkUpdate,
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return homework_service.update_homework(
        db=db,
        school_id=user.school_id,
        homework_id=homework_id,
        current_user=user,
        payload=payload,
    )


@router.post(
    "/{homework_id}/publish",
    response_model=HomeworkResponse,
    dependencies=[Depends(require_permission("homework.publish"))],
)
def publish_homework(
    homework_id: UUID,
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return homework_service.publish_homework(
        db=db,
        school_id=user.school_id,
        homework_id=homework_id,
        current_user=user,
    )


@router.post(
    "/{homework_id}/close",
    response_model=HomeworkResponse,
    dependencies=[Depends(require_permission("homework.update"))],
)
def close_homework(
    homework_id: UUID,
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return homework_service.close_homework(
        db=db,
        school_id=user.school_id,
        homework_id=homework_id,
        current_user=user,
    )


@router.delete(
    "/{homework_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("homework.delete"))],
)
def delete_homework(
    homework_id: UUID,
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    homework_service.delete_homework(
        db=db,
        school_id=user.school_id,
        homework_id=homework_id,
        current_user=user,
    )


@router.post(
    "/{homework_id}/submit",
    response_model=HomeworkSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("homework.submit"))],
)
def submit_homework(
    homework_id: UUID,
    payload: HomeworkSubmissionCreate,
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return homework_service.submit_homework(
        db=db,
        school_id=user.school_id,
        homework_id=homework_id,
        current_user=user,
        payload=payload,
    )


@router.get(
    "/{homework_id}/submissions",
    response_model=HomeworkSubmissionListResponse,
    dependencies=[Depends(require_permission("homework.view"))],
)
def list_homework_submissions(
    homework_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return homework_service.list_submissions_for_homework(
        db=db,
        school_id=user.school_id,
        homework_id=homework_id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/submissions/{submission_id}/grade",
    response_model=HomeworkSubmissionResponse,
    dependencies=[Depends(require_permission("homework.grade"))],
)
def grade_submission(
    submission_id: UUID,
    payload: HomeworkSubmissionGrade,
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return homework_service.grade_submission(
        db=db,
        school_id=user.school_id,
        submission_id=submission_id,
        current_user=user,
        payload=payload,
    )
