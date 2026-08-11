from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.common.enums import TransferCertificateStatus
from app.models.student.transfer_certificate import TransferCertificate
from app.repositories.base import BaseRepository


class TransferCertificateRepository(BaseRepository[TransferCertificate]):
    """
    Repository responsible for TransferCertificate database operations.
    """

    def __init__(self) -> None:
        super().__init__(TransferCertificate)

    def get_by_tc_number(
        self,
        db: Session,
        school_id: UUID,
        tc_number: str,
    ) -> TransferCertificate | None:
        """
        Get active TC by TC number for a school.
        """
        stmt = (
            select(TransferCertificate)
            .where(
                TransferCertificate.school_id == school_id,
                TransferCertificate.tc_number == tc_number,
                TransferCertificate.is_deleted.is_(False),
            )
        )
        return db.scalar(stmt)

    def get_active_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
    ) -> TransferCertificate | None:
        """
        Get active ISSUED TC for a student.
        """
        stmt = (
            select(TransferCertificate)
            .where(
                TransferCertificate.school_id == school_id,
                TransferCertificate.student_id == student_id,
                TransferCertificate.status == TransferCertificateStatus.ISSUED,
                TransferCertificate.is_deleted.is_(False),
            )
        )
        return db.scalar(stmt)

    def get_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
    ) -> list[TransferCertificate]:
        """
        Get all TCs for a student.
        """
        stmt = (
            select(TransferCertificate)
            .where(
                TransferCertificate.school_id == school_id,
                TransferCertificate.student_id == student_id,
                TransferCertificate.is_deleted.is_(False),
            )
            .order_by(TransferCertificate.created_at.desc())
        )
        return list(db.scalars(stmt))

    def get_last_tc_number(
        self,
        db: Session,
        school_id: UUID,
    ) -> TransferCertificate | None:
        """
        Get the latest active TC for a school ordered by creation.
        """
        stmt = (
            select(TransferCertificate)
            .where(
                TransferCertificate.school_id == school_id,
                TransferCertificate.is_deleted.is_(False),
            )
            .order_by(desc(TransferCertificate.created_at))
            .limit(1)
        )
        return db.scalar(stmt)


transfer_certificate_repository = TransferCertificateRepository()
