from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School


class AIUsageLimit(CommonModel):
    """
    Per-school monthly AI token quota tracking and controls.
    """

    __tablename__ = "ai_usage_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    monthly_token_quota: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000000,
    )

    used_tokens_current_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    quota_reset_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship("School")
