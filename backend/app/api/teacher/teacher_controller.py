"""
Teacher Management Controller Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting Teacher entities.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Path,
)
from sqlalchemy.orm import Session

from app.api.teacher.teacher_dependency import (
    get_teacher_service,
)
from app.common.authorization import resolve_user_role_names
from app.common.responses.api_response import (
    ApiResponse,
)
from app.dependencies.database import (
    get_db,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.security.current_user import get_current_user
from app.identity.models import IdentityUser
from app.schemas.teacher import (
    TeacherCreate,
    TeacherFilter,
    TeacherResponse,
    TeacherUpdate,
)
from app.services.teacher.teacher_service import (
    TeacherService,
)

router = APIRouter()


def _redact_teacher_dict(data: dict, current_user: IdentityUser, db: Session) -> dict:
    if getattr(current_user, "is_super_admin", False):
        return data

    role_names = resolve_user_role_names(db, current_user)
    if any(r in ("School Admin", "Principal", "Vice Principal") for r in role_names):
        return data

    user_email = getattr(current_user, "email", None)
    user_phone = getattr(current_user, "phone", None)
    teacher_email = data.get("email")
    teacher_phone = data.get("phone")

    is_self = False
    if user_email and teacher_email and user_email == teacher_email:
        is_self = True
    elif user_phone and teacher_phone and user_phone == teacher_phone:
        is_self = True

    if is_self:
        return data

    # Peer / Non-Admin Redaction
    data["salary"] = None
    if data.get("phone") and len(data["phone"]) >= 4:
        data["phone"] = "XXXXX" + data["phone"][-4:]
    else:
        data["phone"] = None
    data["emergency_contact"] = None
    data["address_line1"] = None
    data["address_line2"] = None
    data["remarks"] = None
    return data


@router.post(
    "",
    response_model=dict,
    summary="Create Teacher",
)
def create_teacher(
    teacher: TeacherCreate,
    current_user: IdentityUser = Depends(require_permission("teacher.create")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Create a new teacher.
    """
    teacher.school_id = current_user.school_id

    created_teacher = service.create_teacher(
        db=db,
        teacher_data=teacher,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=created_teacher.model_dump(mode="json"),
        message="Teacher created successfully.",
    )


@router.get(
    "/me",
    response_model=dict,
    summary="Get Current Teacher Self Profile",
)
def get_current_teacher_profile(
    current_user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """
    Retrieve authenticated teacher user's own profile without administrative scope.
    """
    from sqlalchemy import select, or_
    from app.models.teacher.teacher import Teacher
    from app.common.exceptions import NotFoundException

    conditions = []
    if current_user.email:
        conditions.append(Teacher.email == current_user.email)
    if current_user.phone:
        conditions.append(Teacher.phone == current_user.phone)

    if not conditions:
        raise NotFoundException("Teacher profile not found for current user.")

    teacher = db.scalar(
        select(Teacher).where(
            Teacher.school_id == current_user.school_id,
            Teacher.is_deleted.is_(False),
            or_(*conditions),
        )
    )

    if not teacher:
        raise NotFoundException("Teacher profile not found for current user.")

    return ApiResponse.success(
        data=TeacherResponse.model_validate(teacher).model_dump(mode="json"),
        message="Current teacher profile retrieved successfully.",
    )


@router.get(
    "",
    response_model=dict,
    summary="Get Teachers",
)
def get_teachers(
    filters: TeacherFilter = Depends(),
    current_user: IdentityUser = Depends(require_permission("teacher.view")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Retrieve teachers with filtering and pagination.
    Applies field-level privacy redaction for peer staff views.
    """
    filters.school_id = current_user.school_id

    result = service.get_teachers(
        db=db,
        filters=filters,
        current_school_id=current_user.school_id,
    )

    dumped = result.model_dump(mode="json")
    dumped["items"] = [
        _redact_teacher_dict(item, current_user, db)
        for item in dumped.get("items", [])
    ]

    return ApiResponse.success(
        data=dumped,
        message="Teachers retrieved successfully.",
    )


@router.get(
    "/{teacher_id}",
    response_model=dict,
    summary="Get Teacher by ID",
)
def get_teacher(
    teacher_id: UUID = Path(
        ...,
        description="Teacher ID",
    ),
    current_user: IdentityUser = Depends(require_permission("teacher.view")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Retrieve a teacher by ID.
    Applies field-level privacy redaction for peer staff views.
    """
    teacher = service.get_teacher(
        db=db,
        teacher_id=teacher_id,
        current_school_id=current_user.school_id,
    )

    dumped = teacher.model_dump(mode="json")
    redacted = _redact_teacher_dict(dumped, current_user, db)

    return ApiResponse.success(
        data=redacted,
        message="Teacher retrieved successfully.",
    )


@router.put(
    "/{teacher_id}",
    response_model=dict,
    summary="Update Teacher",
)
def update_teacher(
    teacher: TeacherUpdate = Body(...),
    teacher_id: UUID = Path(
        ...,
        description="Teacher ID",
    ),
    current_user: IdentityUser = Depends(require_permission("teacher.update")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Update an existing teacher.
    """
    updated_teacher = service.update_teacher(
        db=db,
        teacher_id=teacher_id,
        teacher_data=teacher,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=updated_teacher.model_dump(mode="json"),
        message="Teacher updated successfully.",
    )


@router.delete(
    "/{teacher_id}",
    response_model=dict,
    summary="Delete Teacher",
)
def delete_teacher(
    teacher_id: UUID = Path(
        ...,
        description="Teacher ID",
    ),
    current_user: IdentityUser = Depends(require_permission("teacher.delete")),
    db: Session = Depends(get_db),
    service: TeacherService = Depends(get_teacher_service),
) -> dict[str, object]:
    """
    Soft delete a teacher.
    """
    service.delete_teacher(
        db=db,
        teacher_id=teacher_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Teacher deleted successfully.",
    )