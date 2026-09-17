from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database.common_model import CommonModel

if TYPE_CHECKING:
    from app.models.school.school import School


class AIProviderConfig(CommonModel):
    """
    Tenant/System level AI Provider Configuration.
    """

    __tablename__ = "ai_provider_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="MOCK",
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default="mock-default-v1",
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    allow_external_ai: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    encrypted_api_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    api_base_url: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    school: Mapped[School | None] = orm_relationship("School")
