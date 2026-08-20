from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.common.enums import StudentStatus
from app.common.exceptions import NotFoundException, BadRequestException
from app.common.logger.logger import get_logger
from app.identity.models.user import IdentityUser
from app.models.school.school import School
from app.models.student.student import Student
from app.models.student.student_certificate import StudentCertificate, CertificateType
from app.schemas.student.student_certificate import (
    StudentCertificateCreateTC,
    StudentCertificateCreateBonafide,
    StudentCertificateResponse,
    StudentCertificateListResponse,
)

logger = get_logger(__name__)


class StudentCertificateService:

    def _generate_certificate_number(
        self,
        db: Session,
        school_id: UUID,
        certificate_type: CertificateType,
    ) -> str:
        """
        Generate a unique, sequential certificate number per school and type.
        Format: TC-2026-0001 or BC-2026-0001
        """
        current_year = date.today().year
        prefix = "TC" if certificate_type == CertificateType.TRANSFER_CERTIFICATE else "BC"

        stmt = select(func.count(StudentCertificate.id)).where(
            StudentCertificate.school_id == school_id,
            StudentCertificate.certificate_type == certificate_type,
            StudentCertificate.is_deleted.is_(False),
        )
        count = db.scalar(stmt) or 0
        seq = count + 1
        return f"{prefix}-{current_year}-{seq:04d}"

    def issue_transfer_certificate(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        data: StudentCertificateCreateTC,
        issuer: IdentityUser,
    ) -> StudentCertificateResponse:
        """
        Issue Transfer Certificate (TC) for a student and update student status to TRANSFERRED if requested.
        """
        student = db.get(Student, student_id)
        if not student or student.school_id != school_id or student.is_deleted:
            raise NotFoundException(f"Student '{student_id}' not found in school.")

        cert_number = self._generate_certificate_number(
            db,
            school_id=school_id,
            certificate_type=CertificateType.TRANSFER_CERTIFICATE,
        )

        certificate = StudentCertificate(
            school_id=school_id,
            student_id=student.id,
            issued_by_id=issuer.id,
            certificate_type=CertificateType.TRANSFER_CERTIFICATE,
            certificate_number=cert_number,
            issued_date=data.issued_date,
            reason_for_leaving=data.reason_for_leaving,
            conduct=data.conduct,
        )
        db.add(certificate)

        if data.update_student_status:
            student.status = StudentStatus.TRANSFERRED

        # Audit event
        from app.services.audit_log_service import audit_log_service
        audit_log_service.log_event(
            db=db,
            user_id=issuer.id,
            user_email=issuer.email,
            school_id=school_id,
            action="STUDENT_TC_ISSUED",
            entity_type="StudentCertificate",
            entity_id=str(certificate.id),
            details={
                "student_id": str(student.id),
                "certificate_number": cert_number,
                "reason": data.reason_for_leaving,
            },
        )

        db.commit()
        db.refresh(certificate)

        return self._to_response(db, certificate, student)

    def issue_bonafide_certificate(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        data: StudentCertificateCreateBonafide,
        issuer: IdentityUser,
    ) -> StudentCertificateResponse:
        """
        Issue Bonafide Certificate for a student.
        """
        student = db.get(Student, student_id)
        if not student or student.school_id != school_id or student.is_deleted:
            raise NotFoundException(f"Student '{student_id}' not found in school.")

        cert_number = self._generate_certificate_number(
            db,
            school_id=school_id,
            certificate_type=CertificateType.BONAFIDE,
        )

        certificate = StudentCertificate(
            school_id=school_id,
            student_id=student.id,
            issued_by_id=issuer.id,
            certificate_type=CertificateType.BONAFIDE,
            certificate_number=cert_number,
            issued_date=data.issued_date,
            purpose=data.purpose,
            conduct=data.conduct,
        )
        db.add(certificate)

        # Audit event
        from app.services.audit_log_service import audit_log_service
        audit_log_service.log_event(
            db=db,
            user_id=issuer.id,
            user_email=issuer.email,
            school_id=school_id,
            action="STUDENT_BONAFIDE_ISSUED",
            entity_type="StudentCertificate",
            entity_id=str(certificate.id),
            details={
                "student_id": str(student.id),
                "certificate_number": cert_number,
                "purpose": data.purpose,
            },
        )

        db.commit()
        db.refresh(certificate)

        return self._to_response(db, certificate, student)

    def list_certificates(
        self,
        db: Session,
        school_id: UUID,
        certificate_type: CertificateType | None = None,
        student_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> StudentCertificateListResponse:
        """
        List issued tenant certificates with pagination.
        """
        stmt = (
            select(StudentCertificate)
            .where(
                StudentCertificate.school_id == school_id,
                StudentCertificate.is_deleted.is_(False),
            )
        )
        if certificate_type:
            stmt = stmt.where(StudentCertificate.certificate_type == certificate_type)
        if student_id:
            stmt = stmt.where(StudentCertificate.student_id == student_id)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(total_stmt) or 0

        offset = (page - 1) * page_size
        items = db.scalars(
            stmt.order_by(StudentCertificate.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).all()

        responses = [self._to_response(db, cert) for cert in items]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return StudentCertificateListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_certificate(
        self,
        db: Session,
        school_id: UUID,
        certificate_id: UUID,
    ) -> StudentCertificateResponse:
        """
        Get single certificate details.
        """
        cert = db.get(StudentCertificate, certificate_id)
        if not cert or cert.school_id != school_id or cert.is_deleted:
            raise NotFoundException("Certificate record not found.")
        return self._to_response(db, cert)

    def get_printable_html(
        self,
        db: Session,
        school_id: UUID,
        certificate_id: UUID,
    ) -> str:
        """
        Generate print-ready A4 HTML document for Transfer or Bonafide Certificate.
        """
        cert = db.get(StudentCertificate, certificate_id)
        if not cert or cert.school_id != school_id or cert.is_deleted:
            raise NotFoundException("Certificate record not found.")

        school = db.get(School, school_id)
        student = db.get(Student, cert.student_id)

        parent_name = f"{student.parent.first_name} {student.parent.last_name}" if student and student.parent else "Parent/Guardian"
        class_name = student.school_class.name if student and student.school_class else "N/A"
        section_name = student.section.name if student and student.section else "N/A"
        school_name = school.name if school else "AI School OS Partner School"
        school_code = school.code if school else "SCH-001"
        issued_date_str = cert.issued_date.strftime("%B %d, %Y")
        dob_str = student.date_of_birth.strftime("%B %d, %Y") if student and student.date_of_birth else "N/A"

        if cert.certificate_type == CertificateType.TRANSFER_CERTIFICATE:
            title = "TRANSFER CERTIFICATE"
            cert_body = f"""
            <p>This is to certify that <strong>{student.first_name} {student.last_name}</strong>, Son/Daughter of <strong>{parent_name}</strong>, was a bonafide student of this institution in Class <strong>{class_name} - {section_name}</strong> bearing Admission No: <strong>{student.admission_number}</strong>.</p>
            <p style="margin-top: 15px;">Date of Birth (as per school records): <strong>{dob_str}</strong></p>
            <p style="margin-top: 15px;">Reason for leaving: <strong>{cert.reason_for_leaving or 'Completed Studies'}</strong></p>
            <p style="margin-top: 15px;">General Conduct & Behavior: <strong>{cert.conduct or 'Good'}</strong></p>
            <p style="margin-top: 15px;">All school dues up to the date of leaving have been fully cleared. He/She is leaving the school with good character.</p>
            """
        else:
            title = "BONAFIDE CERTIFICATE"
            cert_body = f"""
            <p>This is to certify that <strong>{student.first_name} {student.last_name}</strong>, Son/Daughter of <strong>{parent_name}</strong>, is a bonafide student studying in Class <strong>{class_name} - {section_name}</strong> bearing Admission No: <strong>{student.admission_number}</strong> for the academic session.</p>
            <p style="margin-top: 15px;">Date of Birth (as per school records): <strong>{dob_str}</strong></p>
            <p style="margin-top: 15px;">This certificate is issued upon request for the specific purpose of: <strong>{cert.purpose or 'Official Verification'}</strong>.</p>
            <p style="margin-top: 15px;">General Conduct & Character: <strong>{cert.conduct or 'Good'}</strong></p>
            """

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} - {cert.certificate_number}</title>
    <style>
        @page {{ size: A4 portrait; margin: 20mm; }}
        body {{
            font-family: 'Times New Roman', Georgia, serif;
            margin: 0;
            padding: 20px;
            color: #111827;
            background: #ffffff;
        }}
        .certificate-border {{
            border: 8px double #1e3a8a;
            padding: 30px;
            min-h-full;
            box-sizing: border-box;
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #1e3a8a;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .school-name {{
            font-size: 26px;
            font-weight: bold;
            color: #1e3a8a;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0;
        }}
        .school-info {{
            font-size: 13px;
            color: #4b5563;
            margin-top: 4px;
        }}
        .cert-title {{
            font-size: 22px;
            font-weight: bold;
            text-decoration: underline;
            margin-top: 20px;
            margin-bottom: 25px;
            color: #1e3a8a;
            letter-spacing: 2px;
        }}
        .cert-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            font-weight: bold;
            margin-bottom: 30px;
        }}
        .content {{
            font-size: 16px;
            line-height: 1.8;
            text-align: justify;
            min-height: 250px;
        }}
        .signatures {{
            margin-top: 80px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .sig-box {{
            text-align: center;
            width: 200px;
            border-top: 1px solid #374151;
            padding-top: 6px;
            font-size: 14px;
            font-weight: bold;
        }}
        @media print {{
            body {{ padding: 0; background: none; }}
            .no-print {{ display: none !important; }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 20px; text-align: right;">
        <button onclick="window.print()" style="background: #1e3a8a; color: white; border: none; padding: 10px 20px; font-weight: bold; cursor: pointer; border-radius: 4px;">🖨️ Print / Download PDF</button>
    </div>
    <div class="certificate-border">
        <div class="header">
            <h1 class="school-name">{school_name}</h1>
            <div class="school-info">Affiliated Institutional Campus | School Code: {school_code}</div>
            <div class="cert-title">{title}</div>
        </div>

        <div class="cert-meta">
            <div>Certificate No: <span style="font-family: monospace;">{cert.certificate_number}</span></div>
            <div>Date of Issue: <span>{issued_date_str}</span></div>
        </div>

        <div class="content">
            {cert_body}
        </div>

        <div class="signatures">
            <div class="sig-box">Prepared / Verified By</div>
            <div class="sig-box">Official Seal</div>
            <div class="sig-box">Principal Signature</div>
        </div>
    </div>
</body>
</html>"""
        return html_template

    def _to_response(
        self,
        db: Session,
        cert: StudentCertificate,
        student: Student | None = None,
    ) -> StudentCertificateResponse:
        if not student:
            student = db.get(Student, cert.student_id)

        parent_name = f"{student.parent.first_name} {student.parent.last_name}" if student and student.parent else None
        class_name = student.school_class.name if student and student.school_class else None
        section_name = student.section.name if student and student.section else None
        issuer_name = f"{cert.issued_by.email}" if cert.issued_by else "School Administrator"

        return StudentCertificateResponse(
            id=cert.id,
            school_id=cert.school_id,
            student_id=cert.student_id,
            student_name=f"{student.first_name} {student.last_name}" if student else "Student",
            admission_number=student.admission_number if student else None,
            roll_number=student.roll_number if student else None,
            school_class_name=class_name,
            section_name=section_name,
            parent_name=parent_name,
            certificate_type=cert.certificate_type,
            certificate_number=cert.certificate_number,
            issued_date=cert.issued_date,
            purpose=cert.purpose,
            reason_for_leaving=cert.reason_for_leaving,
            conduct=cert.conduct,
            issued_by_name=issuer_name,
        )


student_certificate_service = StudentCertificateService()
