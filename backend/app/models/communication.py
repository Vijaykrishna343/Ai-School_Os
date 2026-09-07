"""
Communication and Notification Models — Phase 8
UserCommunicationPreference, NotificationTemplate, InAppNotificationRead
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.common_model import CommonModel


class UserCommunicationPreference(CommonModel):
    """
    User-specific communication channel and category preferences.
    Enforces multi-tenant isolation via school_id.
    """
    __tablename__ = "user_communication_preferences"

    __table_args__ = (
        UniqueConstraint("school_id", "user_id", name="uq_user_comm_pref_school_user"),
        Index("ix_user_comm_pref_school_user", "school_id", "user_id"),
    )

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Channel preferences
    enable_in_app: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_sms: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_whatsapp: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Category preferences
    enable_attendance: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_fees: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_exams: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_events: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_hostel: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_leave: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_emergency: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Mandatory override
    enable_announcements: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NotificationTemplate(CommonModel):
    """
    School-specific or global notification template.
    Supports variables like {{student_name}}, {{amount}}, {{due_date}}, {{event_title}}.
    """
    __tablename__ = "notification_templates"

    __table_args__ = (
        UniqueConstraint("school_id", "template_key", name="uq_notif_tpl_school_key"),
        Index("ix_notification_templates_school_key", "school_id", "template_key"),
    )

    school_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    template_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ANNOUNCEMENT",
    )  # ATTENDANCE, FEES, EXAMS, EVENTS, HOSTEL, LEAVE, EMERGENCY, ANNOUNCEMENT

    title_template: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body_template: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class InAppNotificationRead(CommonModel):
    """
    Tracking for in-app notification read state per user.
    """
    __tablename__ = "in_app_notification_reads"

    __table_args__ = (
        UniqueConstraint("user_id", "notification_id", name="uq_in_app_read_user_notif"),
        Index("ix_in_app_read_user", "user_id"),
    )

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("identity_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    notification_id: Mapped[UUID] = mapped_column(
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
