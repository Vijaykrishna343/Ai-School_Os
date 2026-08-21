"""
Pydantic schemas for Document Management (Phase 24).
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.document.document import DocumentCategory, DocumentStatus, OwnerType


class DocumentBase(BaseModel):
    title: str = Field(..., max_length=255)
    document_type: DocumentCategory = DocumentCategory.OTHER


class DocumentCreate(DocumentBase):
    owner_type: OwnerType
    owner_id: UUID


class DocumentUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    document_type: DocumentCategory | None = None


class DocumentVerify(BaseModel):
    pass


class DocumentReject(BaseModel):
    rejection_reason: str = Field(..., min_length=3, max_length=1000)


class DocumentResponse(DocumentBase):
    id: UUID
    school_id: UUID
    owner_type: OwnerType
    owner_id: UUID
    document_type: DocumentCategory
    title: str
    original_filename: str
    storage_key: str
    mime_type: str
    file_size: int
    checksum: str
    status: DocumentStatus
    uploaded_by_id: UUID
    uploaded_at: datetime
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None
    version: int
    is_current: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    # Hydrated owner name metadata
    owner_name: str | None = None
    uploaded_by_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DocumentSummaryResponse(BaseModel):
    total_documents: int
    uploaded_count: int
    verified_count: int
    rejected_count: int
    student_documents_count: int
    staff_documents_count: int
