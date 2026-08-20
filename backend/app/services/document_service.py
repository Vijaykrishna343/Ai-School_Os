"""
Document Service — Business logic for secure private document management (Phase 24).
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.common.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.identity.models.user import IdentityUser
from app.models.audit_log import AuditLog
from app.models.document.document import Document, DocumentCategory, DocumentStatus, OwnerType
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.schemas.document.document import (
    DocumentCategory as SchemaDocumentCategory,
    DocumentListResponse,
    DocumentReject,
    DocumentResponse,
    DocumentSummaryResponse,
    DocumentUpdate,
)
from app.services.storage_service import storage_service


class DocumentService:
    def _audit_log(
        self,
        db: Session,
        school_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        action: str,
        entity_id: str,
        details: str,
    ) -> None:
        """Helper to create audit log records for document actions."""
        try:
            log_entry = AuditLog(
                school_id=school_id,
                user_id=current_user.id,
                user_email=current_user.email,
                role_name=user_role,
                action=action,
                module="DOCUMENTS",
                entity_type="DOCUMENT",
                entity_id=str(entity_id),
                status_code=200,
                details=details,
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            db.rollback()

    def validate_owner_access(
        self,
        db: Session,
        school_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        owner_type: OwnerType,
        owner_id: UUID,
    ) -> None:
        """
        Validates whether current_user is authorized to access documents for owner_id.
        Enforces Parent-Child relationships, Student self-access, and Staff boundary rules.
        """
        # Super Admin platform bypass
        if current_user.is_super_admin:
            return

        # School Admins, Principals, Vice Principals have full access within their school
        if user_role in ("School Admin", "Principal", "Vice Principal"):
            return

        # Parent Role: Must be related to the target student
        if user_role == "Parent":
            if owner_type != OwnerType.STUDENT:
                raise ForbiddenException("Parents can only access student documents.")

            parent = db.scalar(
                select(Parent).where(Parent.email == current_user.email, Parent.school_id == school_id)
            )
            if not parent:
                raise ForbiddenException("Parent profile not found for current user.")

            child = db.scalar(
                select(Student).where(
                    Student.id == owner_id,
                    Student.parent_id == parent.id,
                    Student.school_id == school_id,
                )
            )
            if not child:
                raise ForbiddenException("Access denied. You can only access documents belonging to your children.")
            return

        # Student Role: Must match own student ID
        if user_role == "Student":
            if owner_type != OwnerType.STUDENT:
                raise ForbiddenException("Students can only access student documents.")

            student = db.scalar(
                select(Student).where(Student.email == current_user.email, Student.school_id == school_id)
            )
            if not student or student.id != owner_id:
                raise ForbiddenException("Access denied. You can only access your own documents.")
            return

        # Teacher / Class Teacher: Access allowed for student documents or own staff document
        if user_role in ("Teacher", "Class Teacher"):
            if owner_type == OwnerType.STAFF:
                teacher = db.scalar(
                    select(Teacher).where(Teacher.email == current_user.email, Teacher.school_id == school_id)
                )
                if teacher and teacher.id != owner_id:
                    raise ForbiddenException("Teachers cannot access other staff members' private documents.")
            return

        # Receptionist: Allowed for front-office operations within school
        if user_role == "Receptionist":
            return

    def _hydrate_document_response(self, db: Session, doc: Document) -> DocumentResponse:
        """Hydrates owner_name and uploaded_by_name for frontend display."""
        owner_name = None
        if doc.owner_type == OwnerType.STUDENT:
            st = db.get(Student, doc.owner_id)
            if st:
                owner_name = f"{st.first_name} {st.last_name or ''}".strip()
        elif doc.owner_type == OwnerType.STAFF:
            t = db.get(Teacher, doc.owner_id)
            if t:
                owner_name = f"{t.first_name} {t.last_name or ''}".strip()

        uploader = db.get(IdentityUser, doc.uploaded_by_id)
        uploader_name = (
            f"{uploader.first_name} {uploader.last_name or ''}".strip() if uploader else "System"
        )

        res = DocumentResponse.model_validate(doc)
        res.owner_name = owner_name
        res.uploaded_by_name = uploader_name
        return res

    def upload_document(
        self,
        db: Session,
        school_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        owner_type: OwnerType,
        owner_id: UUID,
        document_type: DocumentCategory,
        title: str,
        file: UploadFile,
    ) -> DocumentResponse:
        """
        Uploads and creates a new document record.
        """
        self.validate_owner_access(db, school_id, current_user, user_role, owner_type, owner_id)

        file_bytes = file.file.read()
        filename = file.filename or "document"
        content_type = file.content_type or "application/octet-stream"

        clean_filename, mime_type = storage_service.validate_file_security(
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )

        storage_key, checksum = storage_service.store_file(
            school_id=school_id,
            owner_type=owner_type.value,
            owner_id=owner_id,
            file_bytes=file_bytes,
            original_filename=clean_filename,
        )

        doc = Document(
            school_id=school_id,
            owner_type=owner_type,
            owner_id=owner_id,
            document_type=document_type,
            title=title.strip() or clean_filename,
            original_filename=clean_filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size=len(file_bytes),
            checksum=checksum,
            status=DocumentStatus.UPLOADED,
            uploaded_by_id=current_user.id,
            uploaded_at=datetime.now(timezone.utc),
            version=1,
            is_current=True,
            is_deleted=False,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        self._audit_log(
            db,
            school_id,
            current_user,
            user_role,
            "UPLOAD_DOCUMENT",
            str(doc.id),
            f"Uploaded document '{doc.title}' ({doc.document_type.value}) for {owner_type.value} ID {owner_id}.",
        )

        return self._hydrate_document_response(db, doc)

    def list_documents(
        self,
        db: Session,
        school_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        page: int = 1,
        page_size: int = 20,
        owner_type: OwnerType | None = None,
        owner_id: UUID | None = None,
        document_type: DocumentCategory | None = None,
        status: DocumentStatus | None = None,
    ) -> DocumentListResponse:
        """
        Lists documents with tenant isolation and role-scoped relationship authorization.
        """
        stmt = select(Document).where(
            Document.school_id == school_id,
            Document.is_deleted.is_(False),
            Document.is_current.is_(True),
        )

        # Apply Parent / Student relationship scoping
        if user_role == "Parent":
            parent = db.scalar(
                select(Parent).where(Parent.email == current_user.email, Parent.school_id == school_id)
            )
            if parent:
                children = db.scalars(
                    select(Student).where(Student.parent_id == parent.id, Student.school_id == school_id)
                ).all()
                child_ids = [c.id for c in children]
                stmt = stmt.where(Document.owner_type == OwnerType.STUDENT, Document.owner_id.in_(child_ids))
            else:
                stmt = stmt.where(Document.id.is_(None))

        elif user_role == "Student":
            student = db.scalar(
                select(Student).where(Student.email == current_user.email, Student.school_id == school_id)
            )
            if student:
                stmt = stmt.where(Document.owner_type == OwnerType.STUDENT, Document.owner_id == student.id)
            else:
                stmt = stmt.where(Document.id.is_(None))

        else:
            if owner_type:
                stmt = stmt.where(Document.owner_type == owner_type)
            if owner_id:
                stmt = stmt.where(Document.owner_id == owner_id)

        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if status:
            stmt = stmt.where(Document.status == status)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Pagination
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        items = db.scalars(stmt).all()

        hydrated_items = [self._hydrate_document_response(db, doc) for doc in items]
        pages = math.ceil(total / page_size) if total > 0 else 1

        return DocumentListResponse(
            items=hydrated_items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_document_by_id(
        self,
        db: Session,
        school_id: UUID,
        document_id: UUID,
        current_user: IdentityUser,
        user_role: str,
    ) -> Document:
        """
        Retrieves a document record ensuring school_id tenant isolation & authorization.
        """
        doc = db.scalar(
            select(Document).where(
                Document.id == document_id,
                Document.school_id == school_id,
                Document.is_deleted.is_(False),
            )
        )
        if not doc:
            raise NotFoundException("Document not found or deleted.")

        self.validate_owner_access(db, school_id, current_user, user_role, doc.owner_type, doc.owner_id)
        return doc

    def get_document_file_content(
        self,
        db: Session,
        school_id: UUID,
        document_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        is_preview: bool = False,
    ) -> tuple[bytes, str, str]:
        """
        Reads private document file bytes for authenticated download/preview.
        Returns (bytes, filename, mime_type).
        """
        doc = self.get_document_by_id(db, school_id, document_id, current_user, user_role)
        file_bytes = storage_service.read_file(doc.storage_key)

        action_name = "PREVIEW_DOCUMENT" if is_preview else "DOWNLOAD_DOCUMENT"
        self._audit_log(
            db,
            school_id,
            current_user,
            user_role,
            action_name,
            str(doc.id),
            f"{action_name} for document '{doc.title}' ({doc.original_filename}).",
        )

        return file_bytes, doc.original_filename, doc.mime_type

    def update_document_metadata(
        self,
        db: Session,
        school_id: UUID,
        document_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        payload: DocumentUpdate,
    ) -> DocumentResponse:
        """Updates document title or document_type category."""
        doc = self.get_document_by_id(db, school_id, document_id, current_user, user_role)

        if payload.title is not None:
            doc.title = payload.title.strip()
        if payload.document_type is not None:
            doc.document_type = payload.document_type

        db.commit()
        db.refresh(doc)

        self._audit_log(
            db,
            school_id,
            current_user,
            user_role,
            "UPDATE_DOCUMENT",
            str(doc.id),
            f"Updated metadata for document '{doc.title}'.",
        )

        return self._hydrate_document_response(db, doc)

    def replace_document(
        self,
        db: Session,
        school_id: UUID,
        document_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        file: UploadFile,
    ) -> DocumentResponse:
        """
        Replaces document file with new version, archiving previous version.
        """
        existing_doc = self.get_document_by_id(db, school_id, document_id, current_user, user_role)

        file_bytes = file.file.read()
        filename = file.filename or "document"
        content_type = file.content_type or "application/octet-stream"

        clean_filename, mime_type = storage_service.validate_file_security(
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )

        storage_key, checksum = storage_service.store_file(
            school_id=school_id,
            owner_type=existing_doc.owner_type.value,
            owner_id=existing_doc.owner_id,
            file_bytes=file_bytes,
            original_filename=clean_filename,
        )

        # Archive old version
        existing_doc.is_current = False

        # Create new version
        new_doc = Document(
            school_id=school_id,
            owner_type=existing_doc.owner_type,
            owner_id=existing_doc.owner_id,
            document_type=existing_doc.document_type,
            title=existing_doc.title,
            original_filename=clean_filename,
            storage_key=storage_key,
            mime_type=mime_type,
            file_size=len(file_bytes),
            checksum=checksum,
            status=DocumentStatus.UPLOADED,
            uploaded_by_id=current_user.id,
            uploaded_at=datetime.now(timezone.utc),
            version=existing_doc.version + 1,
            is_current=True,
            is_deleted=False,
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        self._audit_log(
            db,
            school_id,
            current_user,
            user_role,
            "REPLACE_DOCUMENT",
            str(new_doc.id),
            f"Replaced document '{new_doc.title}' with new version {new_doc.version}.",
        )

        return self._hydrate_document_response(db, new_doc)

    def verify_document(
        self,
        db: Session,
        school_id: UUID,
        document_id: UUID,
        current_user: IdentityUser,
        user_role: str,
    ) -> DocumentResponse:
        """Marks document as VERIFIED."""
        doc = self.get_document_by_id(db, school_id, document_id, current_user, user_role)
        doc.status = DocumentStatus.VERIFIED
        doc.verified_by_id = current_user.id
        doc.verified_at = datetime.now(timezone.utc)
        doc.rejection_reason = None

        db.commit()
        db.refresh(doc)

        self._audit_log(
            db,
            school_id,
            current_user,
            user_role,
            "VERIFY_DOCUMENT",
            str(doc.id),
            f"Verified document '{doc.title}'.",
        )

        return self._hydrate_document_response(db, doc)

    def reject_document(
        self,
        db: Session,
        school_id: UUID,
        document_id: UUID,
        current_user: IdentityUser,
        user_role: str,
        payload: DocumentReject,
    ) -> DocumentResponse:
        """Marks document as REJECTED with rejection reason."""
        doc = self.get_document_by_id(db, school_id, document_id, current_user, user_role)
        doc.status = DocumentStatus.REJECTED
        doc.verified_by_id = current_user.id
        doc.verified_at = datetime.now(timezone.utc)
        doc.rejection_reason = payload.rejection_reason.strip()

        db.commit()
        db.refresh(doc)

        self._audit_log(
            db,
            school_id,
            current_user,
            user_role,
            "REJECT_DOCUMENT",
            str(doc.id),
            f"Rejected document '{doc.title}'. Reason: {doc.rejection_reason}",
        )

        return self._hydrate_document_response(db, doc)

    def soft_delete_document(
        self,
        db: Session,
        school_id: UUID,
        document_id: UUID,
        current_user: IdentityUser,
        user_role: str,
    ) -> None:
        """Soft-deletes a document record and marks is_current=False."""
        doc = self.get_document_by_id(db, school_id, document_id, current_user, user_role)
        doc.is_deleted = True
        doc.is_current = False
        db.commit()

        self._audit_log(
            db,
            school_id,
            current_user,
            user_role,
            "DELETE_DOCUMENT",
            str(doc.id),
            f"Soft-deleted document '{doc.title}'.",
        )

    def get_document_summary(
        self,
        db: Session,
        school_id: UUID,
    ) -> DocumentSummaryResponse:
        """Retrieves document summary metrics for tenant."""
        total = db.scalar(
            select(func.count(Document.id)).where(Document.school_id == school_id, Document.is_deleted.is_(False), Document.is_current.is_(True))
        ) or 0

        uploaded = db.scalar(
            select(func.count(Document.id)).where(
                Document.school_id == school_id, Document.status == DocumentStatus.UPLOADED, Document.is_deleted.is_(False), Document.is_current.is_(True)
            )
        ) or 0

        verified = db.scalar(
            select(func.count(Document.id)).where(
                Document.school_id == school_id, Document.status == DocumentStatus.VERIFIED, Document.is_deleted.is_(False), Document.is_current.is_(True)
            )
        ) or 0

        rejected = db.scalar(
            select(func.count(Document.id)).where(
                Document.school_id == school_id, Document.status == DocumentStatus.REJECTED, Document.is_deleted.is_(False), Document.is_current.is_(True)
            )
        ) or 0

        student_count = db.scalar(
            select(func.count(Document.id)).where(
                Document.school_id == school_id, Document.owner_type == OwnerType.STUDENT, Document.is_deleted.is_(False), Document.is_current.is_(True)
            )
        ) or 0

        staff_count = db.scalar(
            select(func.count(Document.id)).where(
                Document.school_id == school_id, Document.owner_type == OwnerType.STAFF, Document.is_deleted.is_(False), Document.is_current.is_(True)
            )
        ) or 0

        return DocumentSummaryResponse(
            total_documents=total,
            uploaded_count=uploaded,
            verified_count=verified,
            rejected_count=rejected,
            student_documents_count=student_count,
            staff_documents_count=staff_count,
        )


document_service = DocumentService()
