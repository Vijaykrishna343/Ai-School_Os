"""
Document model definition for Phase 24 — Student & Staff Document Management.
"""
from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.common_model import CommonModel


class OwnerType(str, enum.Enum):
    STUDENT = "STUDENT"
    STAFF = "STAFF"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class DocumentCategory(str, enum.Enum):
    # Student Document Categories
    BIRTH_CERTIFICATE = "BIRTH_CERTIFICATE"
    STUDENT_ID = "STUDENT_ID"
    PREVIOUS_SCHOOL_CERT = "PREVIOUS_SCHOOL_CERT"
    TRANSFER_CERTIFICATE = "TRANSFER_CERTIFICATE"
    BONAFIDE_CERTIFICATE = "BONAFIDE_CERTIFICATE"
    PASSPORT_PHOTO = "PASSPORT_PHOTO"
    ADMISSION_DOC = "ADMISSION_DOC"
    # Staff Document Categories
    QUALIFICATION_CERT = "QUALIFICATION_CERT"
    EXPERIENCE_CERT = "EXPERIENCE_CERT"
    IDENTITY_DOC = "IDENTITY_DOC"
    JOINING_DOC = "JOINING_DOC"
    APPOINTMENT_DOC = "APPOINTMENT_DOC"
    OTHER = "OTHER"


class Document(CommonModel):
    """
    Represents a private document associated with a Student or Staff member.
    Enforces tenant isolation via school_id.
    """
    __tablename__ = "documents"

    __table_args__ = (
        Index("ix_documents_school_id", "school_id"),
        Index("ix_documents_owner", "owner_type", "owner_id"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_category", "document_type"),
    )

    school_id: Mapped[UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
    )

    owner_type: Mapped[OwnerType] = mapped_column(
        SQLEnum(OwnerType, native_enum=False, create_type=False),
        nullable=False,
    )

    owner_id: Mapped[UUID] = mapped_column(
        nullable=False,
    )

    document_type: Mapped[DocumentCategory] = mapped_column(
        SQLEnum(DocumentCategory, native_enum=False, create_type=False),
        default=DocumentCategory.OTHER,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        unique=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    checksum: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus, native_enum=False, create_type=False),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )

    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        nullable=False,
    )

    verified_by_id: Mapped[UUID | None] = mapped_column(
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    is_current: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
