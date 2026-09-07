from __future__ import annotations

import uuid
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException, BadRequestException
from app.identity.models.user import IdentityUser


class AITenantBoundaryService:
    """
    Enforces strict tenant boundaries for all AI operations.
    Derives school context from the authenticated user.
    """

    @staticmethod
    def validate_and_get_school_id(current_user: IdentityUser, target_school_id: uuid.UUID | None = None) -> uuid.UUID:
        if not current_user or not current_user.school_id:
            raise ForbiddenException("Authentication and active school context are required for AI operations.")

        user_school_id = current_user.school_id

        if target_school_id is not None and target_school_id != user_school_id:
            raise ForbiddenException("Cross-tenant AI operations are strictly prohibited.")

        return user_school_id

    @staticmethod
    def validate_entity_tenant_scope(db: Session, school_id: uuid.UUID, entity_school_id: uuid.UUID) -> None:
        if school_id != entity_school_id:
            raise ForbiddenException("AI operation attempted to access entity outside tenant boundary.")
