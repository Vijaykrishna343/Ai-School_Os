"""
Document Management API Router (Phase 24).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.current_user import get_current_user
from app.models.document.document import DocumentCategory, DocumentStatus, OwnerType
from app.schemas.document.document import (
    DocumentListResponse,
    DocumentReject,
    DocumentResponse,
    DocumentSummaryResponse,
    DocumentUpdate,
)
from app.services.document_service import document_service

router = APIRouter()


def get_current_user_with_role(
    user: IdentityUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> tuple[IdentityUser, str]:
    """Helper dependency to resolve user and primary role name."""
    user_role = db.scalar(
        select(IdentityUserRole).where(IdentityUserRole.user_id == user.id)
    )
    role_name = "Teacher"
    if user_role:
        role = db.get(IdentityRole, user_role.role_id)
        if role:
            role_name = role.name
    return user, role_name


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("documents.upload"))],
)
def upload_document(
    owner_type: OwnerType = Form(...),
    owner_id: UUID = Form(...),
    document_type: DocumentCategory = Form(DocumentCategory.OTHER),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    return document_service.upload_document(
        db=db,
        school_id=user.school_id,
        current_user=user,
        user_role=role_name,
        owner_type=owner_type,
        owner_id=owner_id,
        document_type=document_type,
        title=title,
        file=file,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    dependencies=[Depends(require_permission("documents.view"))],
)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    owner_type: OwnerType | None = Query(None),
    owner_id: UUID | None = Query(None),
    document_type: DocumentCategory | None = Query(None),
    status: DocumentStatus | None = Query(None),
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    return document_service.list_documents(
        db=db,
        school_id=user.school_id,
        current_user=user,
        user_role=role_name,
        page=page,
        page_size=page_size,
        owner_type=owner_type,
        owner_id=owner_id,
        document_type=document_type,
        status=status,
    )


@router.get(
    "/summary",
    response_model=DocumentSummaryResponse,
    dependencies=[Depends(require_permission("documents.view"))],
)
def get_document_summary(
    db: Session = Depends(get_db),
    user: IdentityUser = Depends(get_current_user),
):
    return document_service.get_document_summary(
        db=db,
        school_id=user.school_id,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    dependencies=[Depends(require_permission("documents.view"))],
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    doc = document_service.get_document_by_id(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
    )
    return document_service._hydrate_document_response(db, doc)


@router.get(
    "/{document_id}/download",
    dependencies=[Depends(require_permission("documents.download"))],
)
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    file_bytes, filename, mime_type = document_service.get_document_file_content(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
        is_preview=False,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Content-Type-Options": "nosniff",
    }
    return Response(content=file_bytes, media_type=mime_type, headers=headers)


@router.get(
    "/{document_id}/preview",
    dependencies=[Depends(require_permission("documents.download"))],
)
def preview_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    file_bytes, filename, mime_type = document_service.get_document_file_content(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
        is_preview=True,
    )
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
    }
    return Response(content=file_bytes, media_type=mime_type, headers=headers)


@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
    dependencies=[Depends(require_permission("documents.update"))],
)
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    return document_service.update_document_metadata(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
        payload=payload,
    )


@router.post(
    "/{document_id}/replace",
    response_model=DocumentResponse,
    dependencies=[Depends(require_permission("documents.upload"))],
)
def replace_document(
    document_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    return document_service.replace_document(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
        file=file,
    )


@router.post(
    "/{document_id}/verify",
    response_model=DocumentResponse,
    dependencies=[Depends(require_permission("documents.verify"))],
)
def verify_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    return document_service.verify_document(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
    )


@router.post(
    "/{document_id}/reject",
    response_model=DocumentResponse,
    dependencies=[Depends(require_permission("documents.verify"))],
)
def reject_document(
    document_id: UUID,
    payload: DocumentReject,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    return document_service.reject_document(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
        payload=payload,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("documents.delete"))],
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    user_context: tuple[IdentityUser, str] = Depends(get_current_user_with_role),
):
    user, role_name = user_context
    document_service.soft_delete_document(
        db=db,
        school_id=user.school_id,
        document_id=document_id,
        current_user=user,
        user_role=role_name,
    )
