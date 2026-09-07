from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.identity.models.user import IdentityUser
    from app.models.school.school import School


class AIAuditLog(CommonModel):
    """
    Immutable audit record of AI operations for privacy, security, and cost tracking.
    Does NOT store sensitive credentials, passwords, JWTs, or raw database results.
    """

    __tablename__ = "ai_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    capability: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    estimated_cost_usd: Mapped[float] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=0.0,
    )

    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SUCCESS",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    school: Mapped[School] = orm_relationship("School")
    user: Mapped[IdentityUser] = orm_relationship("IdentityUser")
