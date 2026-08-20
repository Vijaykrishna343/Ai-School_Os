"""
Notification model definitions.
"""
from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.common_model import CommonModel


class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NotificationRecipientType(str, enum.Enum):
    PARENT = "PARENT"
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    STAFF = "STAFF"


class Notification(CommonModel):
    """
    Notification log and dispatch entity.
    One row per outbound notification attempt.
    """
    __tablename__ = "notifications"

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recipient_type: Mapped[NotificationRecipientType] = mapped_column(
        Enum(NotificationRecipientType, name="notificationrecipienttype"),
        nullable=False,
        index=True,
    )

    recipient_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )

    recipient_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    recipient_contact: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notificationchannel"),
        nullable=False,
        default=NotificationChannel.IN_APP,
        index=True,
    )

    template_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notificationstatus"),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
