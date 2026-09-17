"""
Executive Reports & BI Analytics Service — Phase 30.2
Provides aggregated, role-aware, strictly tenant-isolated reporting metrics across ERP domains.
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import (
    and_,
    case,
    cast,
    desc,
    func,
    or_,
    select,
    String,
)
from sqlalchemy.orm import Session

from app.common.enums.admissions import AdmissionApplicationStatus
from app.common.enums.fees import FeeCategory
from app.common.enums.library import BookCopyStatus, BookLoanStatus
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.admissions.admission_application import AdmissionApplication
from app.models.attendance.attendance import Attendance, AttendanceStatus
from app.models.fees.fee_payment import FeePayment, PaymentMode
from app.models.fees.fee_structure import FeeItem, FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.grading.report_card import ReportCard, ReportCardStatus
from app.models.hostel.hostel_bed import HostelBed
from app.models.hostel.hostel_room import HostelRoom
from app.models.inventory.item import InventoryItem
from app.models.inventory.stock import InventoryStock
from app.models.library.book import Book
from app.models.library.book_copy import BookCopy
from app.models.library.loan import BookLoan
from app.models.notification import Notification, NotificationStatus
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student, StudentStatus
from app.models.teacher.teacher import Teacher
from app.models.transport.route import TransportRoute
from app.models.transport.student_transport_allocation import StudentTransportAllocation
from app.models.transport.vehicle import Vehicle
from app.models.visitor.reception_inquiry import ReceptionInquiry
from app.schemas.reports import (
    AcademicReportResponse,
    AdmissionsReportResponse,
    AdmissionsStageItem,
    AgingBucketSummary,
    AttendanceReportResponse,
    ChronicAbsenteeItem,
    ClassAttendanceItem,
    ClassEnrollmentItem,
    ClassPerformanceSummaryItem,
    EnrollmentTrendItem,
    ExecutiveKpiCard,
    ExecutiveSummaryResponse,
    FinanceReportResponse,
    HostelOperationsSummary,
    InventoryOperationsSummary,
    LibraryOperationsSummary,
    NotificationOperationsSummary,
    OperationsReportResponse,
    PaymentMethodItem,
    RecentCollectionItem,
    ReportFilterParams,
    StudentEnrollmentReportResponse,
    TransportOperationsSummary,
)


class ReportService:
    """
    Centralized reporting engine for executive & cross-domain business intelligence.
    Strictly isolated per tenant school.
    """

    # -----------------------------------------------------------------------
    # 1. Executive Summary
    # -----------------------------------------------------------------------
    def get_executive_summary(
        self,
        db: Session,
        school_id: UUID,
        filters: Optional[ReportFilterParams] = None,
    ) -> ExecutiveSummaryResponse:
        filters = filters or ReportFilterParams()
        school = db.execute(
            select(School).where(School.id == school_id, School.is_deleted.is_(False))
        ).scalar_one_or_none()
        school_name = school.name if school else "School"

        # Active students count
        students_q = select(func.count(Student.id)).where(
            Student.school_id == school_id,
            Student.is_deleted.is_(False),
            Student.status == StudentStatus.ACTIVE,
        )
        if filters.class_id:
            students_q = students_q.where(Student.school_class_id == filters.class_id)
        if filters.section_id:
            students_q = students_q.where(Student.section_id == filters.section_id)
        active_students = db.execute(students_q).scalar() or 0

        # Active teachers count
        active_teachers = db.execute(
            select(func.count(Teacher.id)).where(
                Teacher.school_id == school_id,
                Teacher.is_deleted.is_(False),
            )
        ).scalar() or 0

        # Active classes count
        active_classes = db.execute(
            select(func.count(SchoolClass.id)).where(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted.is_(False),
            )
        ).scalar() or 0

        # Attendance summary
        att_q = select(
            func.count(Attendance.id).label("total_records"),
            func.count(case((Attendance.status == AttendanceStatus.PRESENT, 1))).label("present_count"),
            func.count(case((Attendance.status == AttendanceStatus.HALF_DAY, 1))).label("half_day_count"),
        ).where(
            Attendance.school_id == school_id,
            Attendance.is_deleted.is_(False),
        )
        if filters.class_id:
            att_q = att_q.where(Attendance.school_class_id == filters.class_id)
        if filters.section_id:
            att_q = att_q.where(Attendance.section_id == filters.section_id)
        if filters.start_date:
            att_q = att_q.where(Attendance.attendance_date >= filters.start_date)
        if filters.end_date:
            att_q = att_q.where(Attendance.attendance_date <= filters.end_date)
        if filters.academic_year_id:
            att_q = att_q.where(Attendance.academic_year_id == filters.academic_year_id)

        att_stats = db.execute(att_q).one()
        total_att_records = att_stats.total_records or 0
        present_count = att_stats.present_count or 0
        half_day_count = att_stats.half_day_count or 0
        effective_present = present_count + (half_day_count * 0.5)
        overall_attendance_pct = (
            round((effective_present / total_att_records) * 100.0, 2)
            if total_att_records > 0
            else 0.0
        )

        # Financial Summary
        # Fees Assigned: sum of student fee items
        assigned_q = (
            select(func.coalesce(func.sum(StudentFeeItem.amount), Decimal("0.00")))
            .select_from(StudentFeeItem)
            .join(StudentFeeAssignment, StudentFeeItem.student_fee_assignment_id == StudentFeeAssignment.id)
            .where(
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.is_deleted.is_(False),
                StudentFeeItem.is_deleted.is_(False),
                StudentFeeItem.is_applicable.is_(True),
            )
        )
        if filters.academic_year_id:
            assigned_q = assigned_q.where(StudentFeeAssignment.academic_year_id == filters.academic_year_id)
        total_assigned = db.execute(assigned_q).scalar() or Decimal("0.00")

        # Fees Collected: sum of fee payments
        collected_q = (
            select(func.coalesce(func.sum(FeePayment.amount), Decimal("0.00")))
            .where(
                FeePayment.school_id == school_id,
                FeePayment.is_deleted.is_(False),
            )
        )
        if filters.start_date:
            collected_q = collected_q.where(FeePayment.payment_date >= filters.start_date)
        if filters.end_date:
            collected_q = collected_q.where(FeePayment.payment_date <= filters.end_date)
        total_collected = db.execute(collected_q).scalar() or Decimal("0.00")

        total_outstanding = max(Decimal("0.00"), total_assigned - total_collected)
        fee_collection_rate = (
            round(float((total_collected / total_assigned) * Decimal("100.0")), 2)
            if total_assigned > Decimal("0.00")
            else 0.0
        )

        # Admissions Summary
        adm_apps_q = select(
            func.count(AdmissionApplication.id).label("total_apps"),
            func.count(case((AdmissionApplication.status == AdmissionApplicationStatus.ENROLLED, 1))).label("enrolled_apps"),
        ).where(
            AdmissionApplication.school_id == school_id,
            AdmissionApplication.is_deleted.is_(False),
        )
        adm_stats = db.execute(adm_apps_q).one()
        admissions_applicants = adm_stats.total_apps or 0
        admissions_enrolled = adm_stats.enrolled_apps or 0

        # Admissions inquiries
        inquiries_q = select(func.count(ReceptionInquiry.id)).where(
            ReceptionInquiry.school_id == school_id,
            ReceptionInquiry.is_deleted.is_(False),
        )
        admissions_inquiries = db.execute(inquiries_q).scalar() or 0

        admissions_conversion_pct = (
            round((admissions_enrolled / admissions_applicants) * 100.0, 2)
            if admissions_applicants > 0
            else 0.0
        )

        # Academic (Report cards publication status)
        rc_q = select(
            func.count(ReportCard.id).label("total_rc"),
            func.count(case((ReportCard.status == ReportCardStatus.PUBLISHED, 1))).label("pub_rc"),
        ).where(
            ReportCard.school_id == school_id,
            ReportCard.is_deleted.is_(False),
        )
        if filters.academic_year_id:
            rc_q = rc_q.where(ReportCard.academic_year_id == filters.academic_year_id)
        if filters.academic_term_id:
            rc_q = rc_q.where(ReportCard.academic_term_id == filters.academic_term_id)
        rc_stats = db.execute(rc_q).one()
        total_rc = rc_stats.total_rc or 0
        pub_rc = rc_stats.pub_rc or 0
        published_rc_pct = (
            round((pub_rc / total_rc) * 100.0, 2) if total_rc > 0 else 0.0
        )

        # Build high-impact KPI cards
        kpi_cards = [
            ExecutiveKpiCard(
                id="active_students",
                title="Active Students",
                value=f"{active_students:,}",
                numeric_value=float(active_students),
                subtext="Total enrolled & active",
                trend_direction="up",
                trend_label="Enrolled",
                status="info",
            ),
            ExecutiveKpiCard(
                id="attendance_rate",
                title="Overall Attendance",
                value=f"{overall_attendance_pct:.1f}%",
                numeric_value=overall_attendance_pct,
                unit="%",
                subtext="Attendance average",
                trend_direction="up" if overall_attendance_pct >= 85 else ("neutral" if overall_attendance_pct >= 75 else "down"),
                trend_label="Target > 85%",
                status="success" if overall_attendance_pct >= 85 else ("warning" if overall_attendance_pct >= 75 else "danger"),
            ),
            ExecutiveKpiCard(
                id="fees_collected",
                title="Fees Collected",
                value=f"${float(total_collected):,.2f}",
                numeric_value=float(total_collected),
                subtext=f"{fee_collection_rate:.1f}% of assigned fees",
                trend_direction="up" if fee_collection_rate >= 80 else "neutral",
                trend_label=f"${float(total_outstanding):,.2f} outstanding",
                status="success" if fee_collection_rate >= 80 else ("warning" if fee_collection_rate >= 50 else "danger"),
            ),
            ExecutiveKpiCard(
                id="admissions_conversion",
                title="Admissions Funnel",
                value=f"{admissions_conversion_pct:.1f}%",
                numeric_value=admissions_conversion_pct,
                unit="%",
                subtext=f"{admissions_enrolled} enrolled / {admissions_applicants} applicants",
                trend_direction="up" if admissions_conversion_pct >= 50 else "neutral",
                trend_label=f"{admissions_inquiries} inquiries",
                status="info",
            ),
            ExecutiveKpiCard(
                id="report_cards_published",
                title="Report Cards Published",
                value=f"{published_rc_pct:.1f}%",
                numeric_value=published_rc_pct,
                unit="%",
                subtext=f"{pub_rc} of {total_rc} cards published",
                trend_direction="up" if published_rc_pct == 100.0 else "neutral",
                trend_label="Academic Publication",
                status="success" if published_rc_pct >= 90 else "warning",
            ),
        ]

        # Operations Highlights
        transport_count = db.execute(
            select(func.count(Vehicle.id)).where(Vehicle.school_id == school_id, Vehicle.is_deleted.is_(False))
        ).scalar() or 0
        library_loans = db.execute(
            select(func.count(BookLoan.id)).where(
                BookLoan.school_id == school_id,
                BookLoan.is_deleted.is_(False),
                BookLoan.status == BookLoanStatus.ISSUED,
            )
        ).scalar() or 0
        low_stock = db.execute(
            select(func.count(InventoryStock.id)).join(
                InventoryItem, InventoryStock.item_id == InventoryItem.id
            ).where(
                InventoryStock.school_id == school_id,
                InventoryStock.is_deleted.is_(False),
                InventoryItem.is_deleted.is_(False),
                InventoryStock.quantity <= InventoryItem.reorder_level,
            )
        ).scalar() or 0

        operations_highlights = {
            "active_vehicles": transport_count,
            "active_library_loans": library_loans,
            "low_stock_alerts": low_stock,
        }

        return ExecutiveSummaryResponse(
            school_id=school_id,
            school_name=school_name,
            generated_at=datetime.now(timezone.utc),
            active_students=active_students,
            active_teachers=active_teachers,
            active_classes=active_classes,
            overall_attendance_pct=overall_attendance_pct,
            total_fees_assigned=float(total_assigned),
            total_fees_collected=float(total_collected),
            total_fees_outstanding=float(total_outstanding),
            fee_collection_rate_pct=fee_collection_rate,
            admissions_inquiries=admissions_inquiries,
            admissions_applicants=admissions_applicants,
            admissions_enrolled=admissions_enrolled,
            admissions_conversion_pct=admissions_conversion_pct,
            published_report_cards_pct=published_rc_pct,
            kpi_cards=kpi_cards,
            operations_highlights=operations_highlights,
        )

    # -----------------------------------------------------------------------
    # 2. Student & Enrollment Report
    # -----------------------------------------------------------------------
    def get_student_enrollment_report(
        self,
        db: Session,
        school_id: UUID,
        filters: Optional[ReportFilterParams] = None,
    ) -> StudentEnrollmentReportResponse:
        filters = filters or ReportFilterParams()

        # Total active / inactive counts
        status_q = select(
            func.count(case((Student.status == StudentStatus.ACTIVE, 1))).label("active_cnt"),
            func.count(case((Student.status != StudentStatus.ACTIVE, 1))).label("inactive_cnt"),
            func.count(Student.id).label("total_cnt"),
        ).where(
            Student.school_id == school_id,
            Student.is_deleted.is_(False),
        )
        if filters.class_id:
            status_q = status_q.where(Student.school_class_id == filters.class_id)
        if filters.section_id:
            status_q = status_q.where(Student.section_id == filters.section_id)

        stats = db.execute(status_q).one()
        active_cnt = stats.active_cnt or 0
        inactive_cnt = stats.inactive_cnt or 0
        total_cnt = stats.total_cnt or 0

        # Gender breakdown
        gender_q = (
            select(Student.gender, func.count(Student.id))
            .where(
                Student.school_id == school_id,
                Student.is_deleted.is_(False),
                Student.status == StudentStatus.ACTIVE,
            )
            .group_by(Student.gender)
        )
        if filters.class_id:
            gender_q = gender_q.where(Student.school_class_id == filters.class_id)
        if filters.section_id:
            gender_q = gender_q.where(Student.section_id == filters.section_id)

        gender_rows = db.execute(gender_q).all()
        gender_dist: Dict[str, int] = {}
        for g_enum, cnt in gender_rows:
            key = str(g_enum.value) if hasattr(g_enum, "value") else str(g_enum or "UNKNOWN")
            gender_dist[key] = cnt

        # Breakdown by Class & Section
        cs_q = (
            select(
                SchoolClass.id.label("class_id"),
                SchoolClass.name.label("class_name"),
                Section.id.label("section_id"),
                Section.name.label("section_name"),
                Section.capacity.label("section_capacity"),
                func.count(Student.id).label("student_count"),
                func.count(case((func.upper(cast(Student.gender, String)) == "MALE", 1))).label("male_count"),
                func.count(case((func.upper(cast(Student.gender, String)) == "FEMALE", 1))).label("female_count"),
                func.count(case((func.upper(cast(Student.gender, String)) == "OTHER", 1))).label("other_count"),
            )
            .select_from(SchoolClass)
            .outerjoin(
                Section,
                and_(
                    Section.school_class_id == SchoolClass.id,
                    Section.is_deleted.is_(False),
                ),
            )
            .outerjoin(
                Student,
                and_(
                    Student.school_class_id == SchoolClass.id,
                    or_(Student.section_id == Section.id, Section.id.is_(None)),
                    Student.is_deleted.is_(False),
                    Student.status == StudentStatus.ACTIVE,
                ),
            )
            .where(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted.is_(False),
            )
            .group_by(
                SchoolClass.id,
                SchoolClass.name,
                Section.id,
                Section.name,
                Section.capacity,
            )
            .order_by(SchoolClass.name, Section.name)
        )
        if filters.class_id:
            cs_q = cs_q.where(SchoolClass.id == filters.class_id)
        if filters.section_id:
            cs_q = cs_q.where(Section.id == filters.section_id)

        cs_rows = db.execute(cs_q).all()
        by_class_section: List[ClassEnrollmentItem] = []
        for r in cs_rows:
            cap = r.section_capacity or 40
            occupancy = round((r.student_count / cap) * 100.0, 1) if cap and cap > 0 else None
            by_class_section.append(
                ClassEnrollmentItem(
                    class_id=r.class_id,
                    class_name=r.class_name,
                    section_id=r.section_id,
                    section_name=r.section_name,
                    student_count=r.student_count or 0,
                    male_count=r.male_count or 0,
                    female_count=r.female_count or 0,
                    other_count=r.other_count or 0,
                    capacity=cap,
                    occupancy_pct=occupancy,
                )
            )

        # Enrollment trends (by month for last 6 months)
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        created_dates = db.execute(
            select(Student.created_at)
            .where(
                Student.school_id == school_id,
                Student.is_deleted.is_(False),
                Student.created_at >= six_months_ago,
            )
        ).scalars().all()
        month_counts: Dict[str, int] = {}
        for d in created_dates:
            if d:
                m_str = d.strftime("%Y-%m")
                month_counts[m_str] = month_counts.get(m_str, 0) + 1

        enrollment_trends = [
            EnrollmentTrendItem(
                period=m_str,
                active_count=active_cnt,
                new_admissions=cnt,
            )
            for m_str, cnt in sorted(month_counts.items())
        ]
        if not enrollment_trends:
            enrollment_trends.append(
                EnrollmentTrendItem(
                    period="Current Term",
                    active_count=active_cnt,
                    new_admissions=active_cnt,
                )
            )

        # Pagination slice for class_section items
        offset = (filters.page - 1) * filters.page_size
        paginated_cs = by_class_section[offset : offset + filters.page_size]

        return StudentEnrollmentReportResponse(
            total_active_students=active_cnt,
            total_inactive_students=inactive_cnt,
            total_students=total_cnt,
            gender_distribution=gender_dist,
            by_class_section=paginated_cs,
            enrollment_trends=enrollment_trends,
            total_items=len(by_class_section),
            page=filters.page,
            page_size=filters.page_size,
        )

    # -----------------------------------------------------------------------
    # 3. Attendance Report
    # -----------------------------------------------------------------------
    def get_attendance_report(
        self,
        db: Session,
        school_id: UUID,
        filters: Optional[ReportFilterParams] = None,
    ) -> AttendanceReportResponse:
        filters = filters or ReportFilterParams()
        eval_date = filters.end_date or date.today()

        # Aggregate attendance counts
        base_q = select(
            func.count(Attendance.id).label("total"),
            func.count(case((Attendance.status == AttendanceStatus.PRESENT, 1))).label("present"),
            func.count(case((Attendance.status == AttendanceStatus.ABSENT, 1))).label("absent"),
            func.count(case((Attendance.status == AttendanceStatus.LATE, 1))).label("late"),
            func.count(case((Attendance.status == AttendanceStatus.HALF_DAY, 1))).label("half_day"),
            func.count(case((Attendance.status == AttendanceStatus.EXCUSED, 1))).label("excused"),
        ).where(
            Attendance.school_id == school_id,
            Attendance.is_deleted.is_(False),
        )
        if filters.class_id:
            base_q = base_q.where(Attendance.school_class_id == filters.class_id)
        if filters.section_id:
            base_q = base_q.where(Attendance.section_id == filters.section_id)
        if filters.academic_year_id:
            base_q = base_q.where(Attendance.academic_year_id == filters.academic_year_id)
        if filters.start_date:
            base_q = base_q.where(Attendance.attendance_date >= filters.start_date)
        if filters.end_date:
            base_q = base_q.where(Attendance.attendance_date <= filters.end_date)

        summary = db.execute(base_q).one()
        total_recs = summary.total or 0
        present = summary.present or 0
        absent = summary.absent or 0
        late = summary.late or 0
        half_day = summary.half_day or 0
        excused = summary.excused or 0

        effective_present = present + (half_day * 0.5)
        overall_pct = (
            round((effective_present / total_recs) * 100.0, 2)
            if total_recs > 0
            else 0.0
        )

        # By class & section breakdown
        cs_att_q = (
            select(
                SchoolClass.id.label("class_id"),
                SchoolClass.name.label("class_name"),
                Section.id.label("section_id"),
                Section.name.label("section_name"),
                func.count(Attendance.id).label("total_records"),
                func.count(case((Attendance.status == AttendanceStatus.PRESENT, 1))).label("present_count"),
                func.count(case((Attendance.status == AttendanceStatus.ABSENT, 1))).label("absent_count"),
                func.count(case((Attendance.status == AttendanceStatus.LATE, 1))).label("late_count"),
                func.count(case((Attendance.status == AttendanceStatus.HALF_DAY, 1))).label("half_day_count"),
                func.count(case((Attendance.status == AttendanceStatus.EXCUSED, 1))).label("excused_count"),
            )
            .select_from(Attendance)
            .join(SchoolClass, Attendance.school_class_id == SchoolClass.id)
            .outerjoin(Section, Attendance.section_id == Section.id)
            .where(
                Attendance.school_id == school_id,
                Attendance.is_deleted.is_(False),
            )
            .group_by(
                SchoolClass.id,
                SchoolClass.name,
                Section.id,
                Section.name,
            )
            .order_by(SchoolClass.name, Section.name)
        )
        if filters.class_id:
            cs_att_q = cs_att_q.where(Attendance.school_class_id == filters.class_id)
        if filters.section_id:
            cs_att_q = cs_att_q.where(Attendance.section_id == filters.section_id)
        if filters.academic_year_id:
            cs_att_q = cs_att_q.where(Attendance.academic_year_id == filters.academic_year_id)
        if filters.start_date:
            cs_att_q = cs_att_q.where(Attendance.attendance_date >= filters.start_date)
        if filters.end_date:
            cs_att_q = cs_att_q.where(Attendance.attendance_date <= filters.end_date)

        cs_rows = db.execute(cs_att_q).all()
        by_class_section = []
        for r in cs_rows:
            tot = r.total_records or 0
            prs = r.present_count or 0
            hd = r.half_day_count or 0
            pct = round(((prs + (hd * 0.5)) / tot) * 100.0, 1) if tot > 0 else 0.0
            by_class_section.append(
                ClassAttendanceItem(
                    class_id=r.class_id,
                    class_name=r.class_name,
                    section_id=r.section_id,
                    section_name=r.section_name,
                    total_students=tot,
                    present_count=prs,
                    absent_count=r.absent_count or 0,
                    late_count=r.late_count or 0,
                    excused_count=r.excused_count or 0,
                    attendance_pct=pct,
                )
            )

        # Chronic Absenteeism (< 75% attendance)
        chronic_q = (
            select(
                Student.id.label("student_id"),
                Student.admission_number,
                Student.first_name,
                Student.last_name,
                SchoolClass.name.label("class_name"),
                func.coalesce(Section.name, "—").label("section_name"),
                func.count(Attendance.id).label("total_days"),
                func.count(case((Attendance.status == AttendanceStatus.PRESENT, 1))).label("present_days"),
                func.count(case((Attendance.status == AttendanceStatus.HALF_DAY, 1))).label("half_days"),
                func.count(case((Attendance.status == AttendanceStatus.ABSENT, 1))).label("absent_days"),
            )
            .select_from(Attendance)
            .join(Student, Attendance.student_id == Student.id)
            .join(SchoolClass, Student.school_class_id == SchoolClass.id)
            .outerjoin(Section, Student.section_id == Section.id)
            .where(
                Attendance.school_id == school_id,
                Attendance.is_deleted.is_(False),
                Student.is_deleted.is_(False),
            )
            .group_by(
                Student.id,
                Student.admission_number,
                Student.first_name,
                Student.last_name,
                SchoolClass.name,
                Section.name,
            )
            .having(func.count(Attendance.id) >= 3)
        )
        if filters.class_id:
            chronic_q = chronic_q.where(Attendance.school_class_id == filters.class_id)
        if filters.section_id:
            chronic_q = chronic_q.where(Attendance.section_id == filters.section_id)

        chronic_rows = db.execute(chronic_q).all()
        chronic_absentees = []
        for r in chronic_rows:
            tot = r.total_days or 0
            prs = (r.present_days or 0) + ((r.half_days or 0) * 0.5)
            pct = round((prs / tot) * 100.0, 1) if tot > 0 else 0.0
            st_name = f"{r.first_name or ''} {r.last_name or ''}".strip() or "Unknown"
            if pct < 75.0:
                chronic_absentees.append(
                    ChronicAbsenteeItem(
                        student_id=r.student_id,
                        admission_number=r.admission_number or "",
                        student_name=st_name,
                        class_name=r.class_name,
                        section_name=r.section_name,
                        total_days=tot,
                        present_days=int(prs),
                        absent_days=r.absent_days or 0,
                        attendance_pct=pct,
                    )
                )


        offset = (filters.page - 1) * filters.page_size
        paginated_cs = by_class_section[offset : offset + filters.page_size]

        return AttendanceReportResponse(
            date_evaluated=eval_date,
            overall_attendance_pct=overall_pct,
            total_expected_students=total_recs,
            total_present=present,
            total_absent=absent,
            total_late=late,
            total_excused=excused,
            by_class_section=paginated_cs,
            chronic_absentee_count=len(chronic_absentees),
            chronic_absentees=chronic_absentees[:50],
            total_items=len(by_class_section),
            page=filters.page,
            page_size=filters.page_size,
        )

    # -----------------------------------------------------------------------
    # 4. Finance Report
    # -----------------------------------------------------------------------
    def get_finance_report(
        self,
        db: Session,
        school_id: UUID,
        filters: Optional[ReportFilterParams] = None,
    ) -> FinanceReportResponse:
        filters = filters or ReportFilterParams()

        # Assigned Fees
        assigned_q = (
            select(
                func.coalesce(func.sum(StudentFeeItem.amount), Decimal("0.00")).label("total_assigned"),
                func.coalesce(
                    func.sum(case((StudentFeeItem.category == FeeCategory.TRANSPORTATION, StudentFeeItem.amount), else_=Decimal("0.00"))),
                    Decimal("0.00"),
                ).label("transport_assigned"),
                func.coalesce(
                    func.sum(case((StudentFeeItem.category == FeeCategory.TUITION, StudentFeeItem.amount), else_=Decimal("0.00"))),
                    Decimal("0.00"),
                ).label("tuition_assigned"),
            )
            .select_from(StudentFeeItem)
            .join(StudentFeeAssignment, StudentFeeItem.student_fee_assignment_id == StudentFeeAssignment.id)
            .where(
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.is_deleted.is_(False),
                StudentFeeItem.is_deleted.is_(False),
                StudentFeeItem.is_applicable.is_(True),
            )
        )
        if filters.academic_year_id:
            assigned_q = assigned_q.where(StudentFeeAssignment.academic_year_id == filters.academic_year_id)

        assigned_stats = db.execute(assigned_q).one()
        total_assigned = assigned_stats.total_assigned or Decimal("0.00")
        transport_assigned = assigned_stats.transport_assigned or Decimal("0.00")
        tuition_assigned = assigned_stats.tuition_assigned or Decimal("0.00")

        # Collected Fees
        collected_q = select(
            func.coalesce(func.sum(FeePayment.amount), Decimal("0.00")),
            func.count(FeePayment.id),
        ).where(
            FeePayment.school_id == school_id,
            FeePayment.is_deleted.is_(False),
        )
        if filters.start_date:
            collected_q = collected_q.where(FeePayment.payment_date >= filters.start_date)
        if filters.end_date:
            collected_q = collected_q.where(FeePayment.payment_date <= filters.end_date)

        coll_stats = db.execute(collected_q).one()
        total_collected = coll_stats[0] or Decimal("0.00")
        total_collections_cnt = coll_stats[1] or 0

        total_outstanding = max(Decimal("0.00"), total_assigned - total_collected)
        coll_rate = (
            round(float((total_collected / total_assigned) * Decimal("100.0")), 2)
            if total_assigned > Decimal("0.00")
            else 0.0
        )

        # Payment Methods Breakdown
        methods_q = (
            select(
                FeePayment.payment_mode,
                func.coalesce(func.sum(FeePayment.amount), Decimal("0.00")).label("mode_amount"),
                func.count(FeePayment.id).label("mode_count"),
            )
            .where(
                FeePayment.school_id == school_id,
                FeePayment.is_deleted.is_(False),
            )
            .group_by(FeePayment.payment_mode)
        )
        if filters.start_date:
            methods_q = methods_q.where(FeePayment.payment_date >= filters.start_date)
        if filters.end_date:
            methods_q = methods_q.where(FeePayment.payment_date <= filters.end_date)

        method_rows = db.execute(methods_q).all()
        payment_methods_breakdown = []
        for r in method_rows:
            mode_str = str(r.payment_mode.value) if hasattr(r.payment_mode, "value") else str(r.payment_mode)
            amt = float(r.mode_amount)
            pct = round((amt / float(total_collected)) * 100.0, 1) if float(total_collected) > 0 else 0.0
            payment_methods_breakdown.append(
                PaymentMethodItem(
                    method=mode_str,
                    total_amount=amt,
                    transaction_count=r.mode_count or 0,
                    percentage_of_total=pct,
                )
            )

        # Aging Buckets (Overdue calculation on assignments)
        today = date.today()
        aging_q = (
            select(
                StudentFeeAssignment.due_date,
                func.coalesce(func.sum(StudentFeeItem.amount), Decimal("0.00")).label("item_amount"),
            )
            .select_from(StudentFeeAssignment)
            .join(StudentFeeItem, StudentFeeItem.student_fee_assignment_id == StudentFeeAssignment.id)
            .where(
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.is_deleted.is_(False),
                StudentFeeItem.is_deleted.is_(False),
            )
            .group_by(StudentFeeAssignment.id, StudentFeeAssignment.due_date)
        )
        aging_rows = db.execute(aging_q).all()
        b_0_30, b_31_60, b_61_90, b_90_plus = Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), Decimal("0.00")
        for r in aging_rows:
            due = r.due_date or today
            days_overdue = (today - due).days
            amt = r.item_amount or Decimal("0.00")
            if days_overdue <= 30:
                b_0_30 += amt
            elif days_overdue <= 60:
                b_31_60 += amt
            elif days_overdue <= 90:
                b_61_90 += amt
            else:
                b_90_plus += amt

        # Scale aging buckets proportionally if partial collections exist
        scale = (total_outstanding / total_assigned) if total_assigned > Decimal("0.00") else Decimal("1.00")
        aging_summary = AgingBucketSummary(
            bucket_0_30_days=round(float(b_0_30 * scale), 2),
            bucket_31_60_days=round(float(b_31_60 * scale), 2),
            bucket_61_90_days=round(float(b_61_90 * scale), 2),
            bucket_90_plus_days=round(float(b_90_plus * scale), 2),
        )

        # Recent Collections Table
        recent_q = (
            select(
                FeePayment.id.label("payment_id"),
                FeePayment.receipt_number,
                Student.first_name,
                Student.last_name,
                Student.admission_number,
                FeePayment.amount,
                FeePayment.payment_mode,
                FeePayment.created_at.label("payment_date"),
                FeeStructure.name.label("fee_type"),
            )
            .select_from(FeePayment)
            .join(StudentFeeAssignment, FeePayment.student_fee_assignment_id == StudentFeeAssignment.id)
            .join(Student, StudentFeeAssignment.student_id == Student.id)
            .join(FeeStructure, StudentFeeAssignment.fee_structure_id == FeeStructure.id)
            .where(
                FeePayment.school_id == school_id,
                FeePayment.is_deleted.is_(False),
            )
            .order_by(desc(FeePayment.created_at))
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        recent_rows = db.execute(recent_q).all()
        recent_collections = [
            RecentCollectionItem(
                payment_id=r.payment_id,
                payment_reference=r.receipt_number,
                student_name=f"{r.first_name or ''} {r.last_name or ''}".strip() or "Student",
                admission_number=r.admission_number or "",
                amount=float(r.amount),
                payment_method=str(r.payment_mode.value) if hasattr(r.payment_mode, "value") else str(r.payment_mode),
                payment_date=r.payment_date or datetime.utcnow(),
                fee_type=r.fee_type or "General Fee",
            )
            for r in recent_rows
        ]

        return FinanceReportResponse(
            total_fees_assigned=float(total_assigned),
            total_fees_collected=float(total_collected),
            total_fees_outstanding=float(total_outstanding),
            collection_rate_pct=coll_rate,
            hostel_fees_collected=0.0,
            transport_fees_collected=float(transport_assigned),
            academic_fees_collected=float(tuition_assigned),
            payment_methods_breakdown=payment_methods_breakdown,
            aging_buckets=aging_summary,
            recent_collections=recent_collections,
            total_collections_count=total_collections_cnt,
            page=filters.page,
            page_size=filters.page_size,
        )

    # -----------------------------------------------------------------------
    # 5. Admissions Report
    # -----------------------------------------------------------------------
    def get_admissions_report(
        self,
        db: Session,
        school_id: UUID,
        filters: Optional[ReportFilterParams] = None,
    ) -> AdmissionsReportResponse:
        filters = filters or ReportFilterParams()

        # Inquiries
        inquiries_q = select(func.count(ReceptionInquiry.id)).where(
            ReceptionInquiry.school_id == school_id,
            ReceptionInquiry.is_deleted.is_(False),
        )
        total_inquiries = db.execute(inquiries_q).scalar() or 0

        # Stage breakdown
        stages_q = (
            select(
                AdmissionApplication.status,
                func.count(AdmissionApplication.id).label("stage_cnt"),
            )
            .where(
                AdmissionApplication.school_id == school_id,
                AdmissionApplication.is_deleted.is_(False),
            )
            .group_by(AdmissionApplication.status)
        )
        stage_rows = db.execute(stages_q).all()

        total_apps = 0
        under_review = 0
        admitted = 0
        enrolled = 0
        rejected = 0

        stage_counts: Dict[str, int] = {}
        for st_enum, cnt in stage_rows:
            st_str = str(st_enum.value) if hasattr(st_enum, "value") else str(st_enum)
            stage_counts[st_str] = cnt
            total_apps += cnt
            if st_str in ("UNDER_REVIEW", "SUBMITTED"):
                under_review += cnt
            elif st_str in ("ADMITTED", "SHORTLISTED"):
                admitted += cnt
            elif st_str == "ENROLLED":
                enrolled += cnt
            elif st_str == "REJECTED":
                rejected += cnt

        stages_breakdown: List[AdmissionsStageItem] = []
        for stage_name, count in stage_counts.items():
            pct = round((count / total_apps) * 100.0, 1) if total_apps > 0 else 0.0
            stages_breakdown.append(
                AdmissionsStageItem(
                    stage=stage_name,
                    stage_label=stage_name.replace("_", " ").title(),
                    count=count,
                    percentage=pct,
                )
            )

        inquiry_to_app_pct = round((total_apps / total_inquiries) * 100.0, 1) if total_inquiries > 0 else 0.0
        app_to_enroll_pct = round((enrolled / total_apps) * 100.0, 1) if total_apps > 0 else 0.0

        return AdmissionsReportResponse(
            total_inquiries=total_inquiries,
            total_applications=total_apps,
            total_under_review=under_review,
            total_admitted=admitted,
            total_enrolled=enrolled,
            total_rejected=rejected,
            inquiry_to_app_conversion_pct=inquiry_to_app_pct,
            app_to_enroll_conversion_pct=app_to_enroll_pct,
            stages_breakdown=stages_breakdown,
            pending_followups_count=under_review,
        )

    # -----------------------------------------------------------------------
    # 6. Academic Report
    # -----------------------------------------------------------------------
    def get_academic_report(
        self,
        db: Session,
        school_id: UUID,
        filters: Optional[ReportFilterParams] = None,
    ) -> AcademicReportResponse:
        filters = filters or ReportFilterParams()

        # Overall summary
        summary_q = select(
            func.count(ReportCard.id).label("total_rc"),
            func.count(case((ReportCard.status == ReportCardStatus.PUBLISHED, 1))).label("pub_rc"),
            func.count(case((ReportCard.status == ReportCardStatus.DRAFT, 1))).label("draft_rc"),
            func.avg(ReportCard.percentage).label("avg_pct"),
            func.avg(ReportCard.gpa).label("avg_gpa"),
        ).where(
            ReportCard.school_id == school_id,
            ReportCard.is_deleted.is_(False),
        )
        if filters.academic_year_id:
            summary_q = summary_q.where(ReportCard.academic_year_id == filters.academic_year_id)
        if filters.academic_term_id:
            summary_q = summary_q.where(ReportCard.academic_term_id == filters.academic_term_id)

        stats = db.execute(summary_q).one()
        total_rc = stats.total_rc or 0
        pub_rc = stats.pub_rc or 0
        draft_rc = stats.draft_rc or 0
        avg_pct = round(float(stats.avg_pct or 0.0), 2)
        pub_pct = round((pub_rc / total_rc) * 100.0, 1) if total_rc > 0 else 0.0

        # Class / section performance breakdown
        cs_q = (
            select(
                SchoolClass.id.label("class_id"),
                SchoolClass.name.label("class_name"),
                Section.id.label("section_id"),
                Section.name.label("section_name"),
                func.count(ReportCard.id).label("total_cards"),
                func.count(case((ReportCard.status == ReportCardStatus.PUBLISHED, 1))).label("pub_cards"),
                func.count(case((ReportCard.status == ReportCardStatus.DRAFT, 1))).label("draft_cards"),
                func.avg(ReportCard.percentage).label("avg_score"),
                func.avg(ReportCard.gpa).label("avg_gpa"),
                func.count(case((ReportCard.percentage >= 40.0, 1))).label("passed_cards"),
            )
            .select_from(ReportCard)
            .join(Student, ReportCard.student_id == Student.id)
            .join(SchoolClass, Student.school_class_id == SchoolClass.id)
            .outerjoin(Section, Student.section_id == Section.id)
            .where(
                ReportCard.school_id == school_id,
                ReportCard.is_deleted.is_(False),
            )
            .group_by(
                SchoolClass.id,
                SchoolClass.name,
                Section.id,
                Section.name,
            )
            .order_by(SchoolClass.name, Section.name)
        )
        if filters.academic_year_id:
            cs_q = cs_q.where(ReportCard.academic_year_id == filters.academic_year_id)
        if filters.academic_term_id:
            cs_q = cs_q.where(ReportCard.academic_term_id == filters.academic_term_id)
        if filters.class_id:
            cs_q = cs_q.where(Student.school_class_id == filters.class_id)
        if filters.section_id:
            cs_q = cs_q.where(Student.section_id == filters.section_id)

        cs_rows = db.execute(cs_q).all()
        by_class_section: List[ClassPerformanceSummaryItem] = []
        total_passed = 0
        for r in cs_rows:
            tc = r.total_cards or 0
            passed = r.passed_cards or 0
            total_passed += passed
            pass_rate = round((passed / tc) * 100.0, 1) if tc > 0 else 0.0
            by_class_section.append(
                ClassPerformanceSummaryItem(
                    class_id=r.class_id,
                    class_name=r.class_name,
                    section_id=r.section_id,
                    section_name=r.section_name,
                    total_report_cards=tc,
                    published_count=r.pub_cards or 0,
                    draft_count=r.draft_cards or 0,
                    average_score_pct=round(float(r.avg_score or 0.0), 2),
                    average_gpa=round(float(r.avg_gpa), 2) if r.avg_gpa else None,
                    pass_rate_pct=pass_rate,
                )
            )

        overall_pass_rate = (
            round((total_passed / total_rc) * 100.0, 1) if total_rc > 0 else 0.0
        )

        offset = (filters.page - 1) * filters.page_size
        paginated_cs = by_class_section[offset : offset + filters.page_size]

        return AcademicReportResponse(
            total_report_cards=total_rc,
            total_published=pub_rc,
            total_draft=draft_rc,
            overall_publication_pct=pub_pct,
            overall_average_score_pct=avg_pct,
            overall_pass_rate_pct=overall_pass_rate,
            by_class_section=paginated_cs,
            total_items=len(by_class_section),
            page=filters.page,
            page_size=filters.page_size,
        )

    # -----------------------------------------------------------------------
    # 7. Operations Report
    # -----------------------------------------------------------------------
    def get_operations_report(
        self,
        db: Session,
        school_id: UUID,
    ) -> OperationsReportResponse:
        # Transport
        veh_count = db.execute(
            select(func.count(Vehicle.id)).where(Vehicle.school_id == school_id, Vehicle.is_deleted.is_(False))
        ).scalar() or 0
        route_count = db.execute(
            select(func.count(TransportRoute.id)).where(TransportRoute.school_id == school_id, TransportRoute.is_deleted.is_(False))
        ).scalar() or 0
        trans_students = db.execute(
            select(func.count(StudentTransportAllocation.id)).where(
                StudentTransportAllocation.school_id == school_id,
                StudentTransportAllocation.is_deleted.is_(False),
            )
        ).scalar() or 0

        transport_summary = TransportOperationsSummary(
            total_vehicles=veh_count,
            total_routes=route_count,
            total_assigned_students=trans_students,
            active_vehicles_count=veh_count,
        )

        # Library
        books_count = db.execute(
            select(func.count(Book.id)).where(
                Book.school_id == school_id, Book.is_deleted.is_(False)
            )
        ).scalar() or 0
        avail_copies = db.execute(
            select(func.count(BookCopy.id)).where(
                BookCopy.school_id == school_id,
                BookCopy.is_deleted.is_(False),
                BookCopy.status == BookCopyStatus.AVAILABLE,
            )
        ).scalar() or 0
        active_loans = db.execute(
            select(func.count(BookLoan.id)).where(
                BookLoan.school_id == school_id,
                BookLoan.is_deleted.is_(False),
                BookLoan.status == BookLoanStatus.ISSUED,
            )
        ).scalar() or 0
        overdue_loans = db.execute(
            select(func.count(BookLoan.id)).where(
                BookLoan.school_id == school_id,
                BookLoan.is_deleted.is_(False),
                BookLoan.status == BookLoanStatus.OVERDUE,
            )
        ).scalar() or 0

        library_summary = LibraryOperationsSummary(
            total_books=books_count,
            active_loans_count=active_loans,
            overdue_loans_count=overdue_loans,
            available_copies_count=avail_copies,
        )

        # Inventory
        total_items = db.execute(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.school_id == school_id, InventoryItem.is_deleted.is_(False)
            )
        ).scalar() or 0
        low_stock_items = db.execute(
            select(func.count(InventoryStock.id)).join(
                InventoryItem, InventoryStock.item_id == InventoryItem.id
            ).where(
                InventoryStock.school_id == school_id,
                InventoryStock.is_deleted.is_(False),
                InventoryItem.is_deleted.is_(False),
                InventoryStock.quantity <= InventoryItem.reorder_level,
                InventoryStock.quantity > 0,
            )
        ).scalar() or 0
        out_of_stock = db.execute(
            select(func.count(InventoryStock.id)).where(
                InventoryStock.school_id == school_id,
                InventoryStock.is_deleted.is_(False),
                InventoryStock.quantity <= 0,
            )
        ).scalar() or 0
        valuation = db.execute(
            select(
                func.coalesce(
                    func.sum(InventoryStock.quantity * func.coalesce(InventoryStock.unit_price, Decimal("0.00"))),
                    Decimal("0.00"),
                )
            ).where(
                InventoryStock.school_id == school_id,
                InventoryStock.is_deleted.is_(False),
            )
        ).scalar() or Decimal("0.00")

        inventory_summary = InventoryOperationsSummary(
            total_items=total_items,
            low_stock_items_count=low_stock_items,
            out_of_stock_items_count=out_of_stock,
            total_inventory_valuation=float(valuation),
        )

        # Hostel
        rooms_count = db.execute(
            select(func.count(HostelRoom.id)).where(
                HostelRoom.school_id == school_id, HostelRoom.is_deleted.is_(False)
            )
        ).scalar() or 0
        capacity_count = db.execute(
            select(func.coalesce(func.sum(HostelRoom.capacity), 0)).where(
                HostelRoom.school_id == school_id, HostelRoom.is_deleted.is_(False)
            )
        ).scalar() or 0
        occupied_count = db.execute(
            select(func.count(HostelBed.id)).where(
                HostelBed.school_id == school_id,
                HostelBed.is_deleted.is_(False),
                HostelBed.status == "OCCUPIED",
            )
        ).scalar() or 0
        hostel_occ_pct = (
            round((occupied_count / capacity_count) * 100.0, 1) if capacity_count > 0 else 0.0
        )

        hostel_summary = HostelOperationsSummary(
            total_rooms=rooms_count,
            total_bed_capacity=capacity_count,
            occupied_beds_count=occupied_count,
            available_beds_count=max(0, capacity_count - occupied_count),
            occupancy_rate_pct=hostel_occ_pct,
        )

        # Notifications
        notif_stats = db.execute(
            select(
                func.count(Notification.id).label("total_sent"),
                func.count(case((Notification.status == NotificationStatus.SENT, 1))).label("delivered"),
                func.count(case((Notification.status == NotificationStatus.PENDING, 1))).label("pending"),
                func.count(case((Notification.status == NotificationStatus.FAILED, 1))).label("failed"),
            ).where(
                Notification.school_id == school_id,
                Notification.is_deleted.is_(False),
            )
        ).one()
        tot_notif = notif_stats.total_sent or 0
        del_notif = notif_stats.delivered or 0
        succ_pct = round((del_notif / tot_notif) * 100.0, 1) if tot_notif > 0 else 0.0

        notifications_summary = NotificationOperationsSummary(
            total_notifications_sent=tot_notif,
            delivered_count=del_notif,
            pending_count=notif_stats.pending or 0,
            failed_count=notif_stats.failed or 0,
            delivery_success_rate_pct=succ_pct,
        )

        return OperationsReportResponse(
            transport=transport_summary,
            library=library_summary,
            inventory=inventory_summary,
            hostel=hostel_summary,
            notifications=notifications_summary,
        )

    # -----------------------------------------------------------------------
    # 8. CSV Export Engine
    # -----------------------------------------------------------------------
    def export_report_csv(
        self,
        db: Session,
        school_id: UUID,
        category: str,
        filters: Optional[ReportFilterParams] = None,
    ) -> Tuple[str, str]:
        filters = filters or ReportFilterParams()
        filters.page = 1
        filters.page_size = 1000  # Export up to 1000 items

        output = io.StringIO()
        filename = f"{category}_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

        if category == "students":
            resp = self.get_student_enrollment_report(db, school_id, filters)
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "class_name",
                    "section_name",
                    "student_count",
                    "male_count",
                    "female_count",
                    "other_count",
                    "capacity",
                    "occupancy_pct",
                ],
            )
            writer.writeheader()
            for item in resp.by_class_section:
                writer.writerow(
                    {
                        "class_name": item.class_name,
                        "section_name": item.section_name or "—",
                        "student_count": item.student_count,
                        "male_count": item.male_count,
                        "female_count": item.female_count,
                        "other_count": item.other_count,
                        "capacity": item.capacity or "—",
                        "occupancy_pct": f"{item.occupancy_pct}%" if item.occupancy_pct else "—",
                    }
                )

        elif category == "attendance":
            resp = self.get_attendance_report(db, school_id, filters)
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "class_name",
                    "section_name",
                    "total_students",
                    "present_count",
                    "absent_count",
                    "late_count",
                    "excused_count",
                    "attendance_pct",
                ],
            )
            writer.writeheader()
            for item in resp.by_class_section:
                writer.writerow(
                    {
                        "class_name": item.class_name,
                        "section_name": item.section_name or "—",
                        "total_students": item.total_students,
                        "present_count": item.present_count,
                        "absent_count": item.absent_count,
                        "late_count": item.late_count,
                        "excused_count": item.excused_count,
                        "attendance_pct": f"{item.attendance_pct}%",
                    }
                )

        elif category == "finance":
            resp = self.get_finance_report(db, school_id, filters)
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "payment_reference",
                    "student_name",
                    "admission_number",
                    "amount",
                    "payment_method",
                    "fee_type",
                    "payment_date",
                ],
            )
            writer.writeheader()
            for item in resp.recent_collections:
                writer.writerow(
                    {
                        "payment_reference": item.payment_reference,
                        "student_name": item.student_name,
                        "admission_number": item.admission_number,
                        "amount": f"{item.amount:.2f}",
                        "payment_method": item.payment_method,
                        "fee_type": item.fee_type,
                        "payment_date": item.payment_date.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

        elif category == "academic":
            resp = self.get_academic_report(db, school_id, filters)
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "class_name",
                    "section_name",
                    "total_report_cards",
                    "published_count",
                    "draft_count",
                    "average_score_pct",
                    "average_gpa",
                    "pass_rate_pct",
                ],
            )
            writer.writeheader()
            for item in resp.by_class_section:
                writer.writerow(
                    {
                        "class_name": item.class_name,
                        "section_name": item.section_name or "—",
                        "total_report_cards": item.total_report_cards,
                        "published_count": item.published_count,
                        "draft_count": item.draft_count,
                        "average_score_pct": f"{item.average_score_pct}%",
                        "average_gpa": item.average_gpa or "—",
                        "pass_rate_pct": f"{item.pass_rate_pct}%",
                    }
                )

        elif category == "admissions":
            resp = self.get_admissions_report(db, school_id, filters)
            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "stage",
                    "stage_label",
                    "count",
                    "percentage",
                ],
            )
            writer.writeheader()
            for item in resp.stages_breakdown:
                writer.writerow(
                    {
                        "stage": item.stage,
                        "stage_label": item.stage_label,
                        "count": item.count,
                        "percentage": f"{item.percentage}%",
                    }
                )

        else:
            # General fallback
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])
            exec_resp = self.get_executive_summary(db, school_id, filters)
            for kpi in exec_resp.kpi_cards:
                writer.writerow([kpi.title, kpi.value])

        return output.getvalue(), filename


report_service = ReportService()
