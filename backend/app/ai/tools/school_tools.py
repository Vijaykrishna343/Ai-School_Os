from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.common.exceptions import NotFoundException, ForbiddenException


def get_school_summary(db: Session, school_id: uuid.UUID, current_user_school_id: uuid.UUID, **kwargs: Any) -> dict[str, Any]:
    """
    Safe demonstration tool returning basic school profile summary.
    Enforces school_id tenant scoping.
    """
    if school_id != current_user_school_id:
        raise ForbiddenException("Cross-tenant tool execution attempt rejected.")

    school = db.scalar(select(School).where(School.id == school_id))
    if not school:
        raise NotFoundException("School profile not found.")

    return {
        "school_id": str(school.id),
        "name": school.name,
        "code": school.code,
        "city": school.city,
        "state": school.state,
    }
