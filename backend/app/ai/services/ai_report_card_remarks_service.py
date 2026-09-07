"""
AI Report Card Remarks Service for Phase 12.6.
Orchestrates quantitative marks & risk signal synthesis into qualitative draft remarks,
PII sanitization, tenant isolation, quota management, database persistence, and audit logging.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.ai.report_card.engine import (
    AIReportCardRemarksEngine,
    ReportCardRemarksInput,
    ReportCardRemarksOutput,
    SubjectMarkItem,
    ai_report_card_remarks_engine,
)
from app.ai.security.data_minimizer import AIDataMinimizer
from app.ai.security.tenant_boundary import AITenantBoundaryService
from app.ai.services.ai_audit_service import ai_audit_service
from app.ai.services.ai_usage_service import ai_usage_service
from app.common.exceptions import ForbiddenException, NotFoundException, BadRequestException
from app.identity.models import IdentityUser
from app.models.ai import AIReportCardRemark, AIStudentRiskAssessment
from app.models.grading import ReportCard, ReportCardItemSnapshot
from app.models.student import Student


class AIReportCardRemarksService:
    """
    Service for AI report card qualitative remarks synthesis and application.
    """

    AUTHORIZED_ROLES = {
        "Super Admin",
        "School Admin",
        "Principal",
        "Vice Principal",
        "Teacher",
    }

    def __init__(self, engine: AIReportCardRemarksEngine = ai_report_card_remarks_engine):
        self.engine = engine

    def _verify_user_role_scope(self, current_user: IdentityUser) -> None:
        """
        Verifies authorized role for editing/generating report card remarks.
        """
        role_names = {r.name for r in current_user.roles}
        is_authorized = any(
            name in self.AUTHORIZED_ROLES or any(auth_role in name for auth_role in self.AUTHORIZED_ROLES)
            for name in role_names
        )
        if not is_authorized:
            raise ForbiddenException("User role is not authorized to generate report card remarks using AI.")

    def generate_remarks(
        self,
        db: Session,
        current_user: IdentityUser,
        report_card_id: uuid.UUID,
        tone: str = "BALANCED",
        detail_level: str = "DETAILED",
    ) -> AIReportCardRemark:
        """
        Generates qualitative evaluation remarks for a specific report card.
        """
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        self._verify_user_role_scope(current_user)

        # 1. Fetch Target Report Card & Related Domain Entities
        report_card = db.query(ReportCard).filter(
            ReportCard.id == report_card_id,
            ReportCard.school_id == school_id,
            ReportCard.is_deleted == False,
        ).first()

        if not report_card:
            raise NotFoundException("Report card record not found.")

        student = db.query(Student).filter(
            Student.id == report_card.student_id,
            Student.school_id == school_id,
            Student.is_deleted == False,
        ).first()

        if not student:
            raise NotFoundException("Student record associated with report card not found.")

        snapshots = db.query(ReportCardItemSnapshot).filter(
            ReportCardItemSnapshot.report_card_id == report_card.id,
            ReportCardItemSnapshot.is_deleted == False,
        ).all()

        # Fetch optional Phase 12.4 Risk Assessment
        risk_assessment = db.query(AIStudentRiskAssessment).filter(
            AIStudentRiskAssessment.student_id == student.id,
            AIStudentRiskAssessment.school_id == school_id,
            AIStudentRiskAssessment.is_deleted == False,
        ).order_by(desc(AIStudentRiskAssessment.assessed_at)).first()

        risk_level = risk_assessment.risk_level if risk_assessment else None

        # 2. PII Sanitization
        sanitized_name, _ = AIDataMinimizer.sanitize_text(student.first_name)
        gender_str = student.gender.value if hasattr(student.gender, 'value') else str(student.gender)

        # 3. Quota Reservation
        ai_usage_service.check_and_reserve_quota(db, school_id)

        # 4. Engine Input Assembly
        subject_items = [
            SubjectMarkItem(
                subject_name=s.subject_name,
                percentage=float(s.percentage) if s.percentage is not None else 0.0,
                grade=getattr(s, "grade_code", None) or getattr(s, "grade", "N/A"),
                is_passed=getattr(s, "is_pass", None) if getattr(s, "is_pass", None) is not None else getattr(s, "is_passed", True),
            )
            for s in snapshots
        ]

        input_data = ReportCardRemarksInput(
            student_name=sanitized_name,
            gender=gender_str,
            percentage=float(report_card.percentage) if report_card.percentage is not None else 0.0,
            overall_grade=report_card.overall_grade or "N/A",
            is_passed=report_card.is_passed,
            attendance_percentage=float(report_card.attendance_percentage) if report_card.attendance_percentage is not None else 100.0,
            subject_marks=subject_items,
            risk_level=risk_level,
            tone=tone,
            detail_level=detail_level,
        )

        output: ReportCardRemarksOutput = self.engine.generate(input_data)

        # 5. Persist Draft Entity in DB
        remark = AIReportCardRemark(
            school_id=school_id,
            report_card_id=report_card.id,
            student_id=student.id,
            created_by_user_id=current_user.id,
            tone=tone,
            detail_level=detail_level,
            teacher_remarks_draft=output.teacher_remarks,
            principal_remarks_draft=output.principal_remarks,
            action_items=output.action_items,
            strength_subjects=output.strength_subjects,
            focus_subjects=output.focus_subjects,
            token_count=output.token_count,
            status="DRAFT",
            assessed_at=datetime.now(timezone.utc),
        )

        db.add(remark)
        db.commit()
        db.refresh(remark)

        # 6. Deduct Token Quota & Record Audit Log
        ai_usage_service.record_usage(db, school_id, output.token_count)
        ai_audit_service.log_ai_event(
            db=db,
            school_id=school_id,
            user_id=current_user.id,
            capability="REPORT_CARD_REMARKS",
            provider_type="MOCK",
            model_name="deterministic-remarks-v1",
            prompt_tokens=max(10, output.token_count // 2),
            completion_tokens=max(10, output.token_count // 2),
            estimated_cost_usd=0.0000,
            latency_ms=12,
            status="SUCCESS",
        )

        return remark

    def apply_remark_to_report_card(
        self,
        db: Session,
        current_user: IdentityUser,
        report_card_id: uuid.UUID,
        teacher_remarks: Optional[str] = None,
        principal_remarks: Optional[str] = None,
    ) -> ReportCard:
        """
        Applies generated or edited AI remarks into the official ReportCard entity.
        """
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        self._verify_user_role_scope(current_user)

        report_card = db.query(ReportCard).filter(
            ReportCard.id == report_card_id,
            ReportCard.school_id == school_id,
            ReportCard.is_deleted == False,
        ).first()

        if not report_card:
            raise NotFoundException("Report card record not found.")

        if teacher_remarks is not None:
            report_card.teacher_remarks = teacher_remarks
        if principal_remarks is not None:
            report_card.principal_remarks = principal_remarks

        db.commit()
        db.refresh(report_card)

        # Update latest remark status to ACCEPTED
        remark = db.query(AIReportCardRemark).filter(
            AIReportCardRemark.report_card_id == report_card.id,
            AIReportCardRemark.school_id == school_id,
            AIReportCardRemark.is_deleted == False,
        ).order_by(desc(AIReportCardRemark.created_at)).first()

        if remark:
            remark.status = "ACCEPTED"
            db.commit()

        return report_card

    def get_remark(
        self,
        db: Session,
        current_user: IdentityUser,
        report_card_id: uuid.UUID,
    ) -> AIReportCardRemark:
        """
        Fetches the latest AI generated remark draft for a report card.
        """
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        self._verify_user_role_scope(current_user)

        remark = db.query(AIReportCardRemark).filter(
            AIReportCardRemark.report_card_id == report_card_id,
            AIReportCardRemark.school_id == school_id,
            AIReportCardRemark.is_deleted == False,
        ).order_by(desc(AIReportCardRemark.created_at)).first()

        if not remark:
            raise NotFoundException("No AI generated remark draft found for this report card.")

        return remark


ai_report_card_remarks_service = AIReportCardRemarksService()
