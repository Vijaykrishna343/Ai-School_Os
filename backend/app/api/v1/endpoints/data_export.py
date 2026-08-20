"""
Data Export Endpoint — Phase 9.4
GET /api/v1/export/{entity_type}
Returns CSV data for authorized school users.
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser

router = APIRouter()


def _val(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (date, datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v)


def _csv_response(rows: list[dict], filename: str, headers_schema: list[str] | None = None) -> StreamingResponse:
    if not rows and not headers_schema:
        # Return empty CSV with just a newline
        return StreamingResponse(
            iter([""]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    output = io.StringIO()
    fieldnames = headers_schema or list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    if rows:
        writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/students", summary="Export Students as CSV")
def export_students(
    status_filter: str | None = Query(default=None, alias="status"),
    class_id: UUID | None = Query(default=None),
    section_id: UUID | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("student.export")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from sqlalchemy import select
    from app.models.student.student import Student
    from app.models.school_class.school_class import SchoolClass
    from app.models.section.section import Section

    q = select(Student).where(
        Student.school_id == current_user.school_id,
        Student.is_deleted.is_(False),
    )
    if status_filter:
        q = q.where(Student.status == status_filter.upper())
    if class_id:
        q = q.where(Student.school_class_id == class_id)
    if section_id:
        q = q.where(Student.section_id == section_id)

    students = db.execute(q.order_by(Student.admission_number)).scalars().all()

    rows = [
        {
            "admission_number": _val(s.admission_number),
            "roll_number": _val(s.roll_number),
            "first_name": _val(s.first_name),
            "middle_name": _val(s.middle_name),
            "last_name": _val(s.last_name),
            "gender": _val(s.gender),
            "date_of_birth": _val(s.date_of_birth),
            "blood_group": _val(s.blood_group),
            "phone": _val(s.phone),
            "email": _val(s.email),
            "address_line1": _val(s.address_line1),
            "city": _val(s.city),
            "district": _val(s.district),
            "state": _val(s.state),
            "country": _val(s.country),
            "status": _val(s.status),
        }
        for s in students
    ]
    student_headers = ["admission_number", "roll_number", "first_name", "middle_name",
                       "last_name", "gender", "date_of_birth", "blood_group",
                       "phone", "email", "address_line1", "city", "district",
                       "state", "country", "status"]
    return _csv_response(rows, "students_export.csv", headers_schema=student_headers)


@router.get("/teachers", summary="Export Teachers as CSV")
def export_teachers(
    current_user: IdentityUser = Depends(require_permission("teacher.export")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from sqlalchemy import select
    from app.models.teacher.teacher import Teacher

    teachers = db.execute(
        select(Teacher).where(
            Teacher.school_id == current_user.school_id,
            Teacher.is_deleted.is_(False),
        ).order_by(Teacher.first_name)
    ).scalars().all()

    rows = [
        {
            "employee_id": _val(t.employee_id),
            "first_name": _val(t.first_name),
            "middle_name": _val(t.middle_name),
            "last_name": _val(t.last_name),
            "gender": _val(t.gender),
            "date_of_birth": _val(t.date_of_birth),
            "phone": _val(t.phone),
            "email": _val(t.email),
            "qualification": _val(t.qualification),
            "specialization": _val(t.specialization),
            "experience_years": _val(t.experience_years),
            "joining_date": _val(t.joining_date),
            "address_line1": _val(t.address_line1),
            "city": _val(t.city),
            "state": _val(t.state),
            "status": _val(t.status),
        }
        for t in teachers
    ]
    return _csv_response(rows, "teachers_export.csv")


@router.get("/parents", summary="Export Parents as CSV")
def export_parents(
    current_user: IdentityUser = Depends(require_permission("parent.export")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from sqlalchemy import select
    from app.models.parent.parent import Parent

    parents = db.execute(
        select(Parent).where(
            Parent.school_id == current_user.school_id,
            Parent.is_deleted.is_(False),
        ).order_by(Parent.father_name)
    ).scalars().all()

    rows = [
        {
            "father_name": _val(p.father_name),
            "mother_name": _val(p.mother_name),
            "guardian_name": _val(p.guardian_name),
            "relationship": _val(p.relationship),
            "primary_phone": _val(p.primary_phone),
            "secondary_phone": _val(p.secondary_phone),
            "email": _val(p.email),
            "occupation": _val(p.occupation),
            "annual_income": _val(p.annual_income),
            "address_line1": _val(p.address_line1),
            "city": _val(p.city),
            "state": _val(p.state),
        }
        for p in parents
    ]
    return _csv_response(rows, "parents_export.csv")


@router.get("/attendance", summary="Export Attendance as CSV")
def export_attendance(
    section_id: UUID | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("attendance.export")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from sqlalchemy import select
    from app.models.attendance.attendance import Attendance
    from app.models.student.student import Student

    q = select(Attendance, Student).join(
        Student, Attendance.student_id == Student.id
    ).where(
        Attendance.school_id == current_user.school_id,
        Attendance.is_deleted.is_(False),
        Student.is_deleted.is_(False),
    )
    if section_id:
        q = q.where(Attendance.section_id == section_id)
    if date_from:
        q = q.where(Attendance.attendance_date >= date_from)
    if date_to:
        q = q.where(Attendance.attendance_date <= date_to)

    q = q.order_by(Attendance.attendance_date, Student.admission_number)
    records = db.execute(q).all()

    rows = [
        {
            "date": _val(att.attendance_date),
            "admission_number": _val(stu.admission_number),
            "Student Name": f"{stu.first_name} {stu.last_name or ''}".strip(),
            "status": _val(att.status),
            "remarks": _val(att.remarks) if hasattr(att, "remarks") else "",
        }
        for att, stu in records
    ]
    attendance_headers = ["date", "admission_number", "Student Name", "status", "remarks"]
    return _csv_response(rows, "attendance_export.csv", headers_schema=attendance_headers)


@router.get("/fees", summary="Export Fee Payments as CSV")
def export_fees(
    academic_year_id: UUID | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("fees.export")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from sqlalchemy import select
    from app.models.fees.fee_payment import FeePayment
    from app.models.fees.student_fee_assignment import StudentFeeAssignment
    from app.models.student.student import Student
    from app.models.fees.fee_structure import FeeStructure

    q = (
        select(FeePayment, StudentFeeAssignment, Student, FeeStructure)
        .join(StudentFeeAssignment, FeePayment.student_fee_assignment_id == StudentFeeAssignment.id)
        .join(Student, StudentFeeAssignment.student_id == Student.id)
        .join(FeeStructure, StudentFeeAssignment.fee_structure_id == FeeStructure.id)
        .where(
            FeePayment.school_id == current_user.school_id,
            FeePayment.is_deleted.is_(False),
        )
    )
    if academic_year_id:
        q = q.where(StudentFeeAssignment.academic_year_id == academic_year_id)
    q = q.order_by(FeePayment.payment_date, Student.admission_number)
    records = db.execute(q).all()

    rows = [
        {
            "receipt_number": _val(fp.receipt_number),
            "payment_date": _val(fp.payment_date),
            "student_name": f"{stu.first_name} {stu.last_name}",
            "admission_number": _val(stu.admission_number),
            "fee_structure": _val(fs.name),
            "amount_paid": _val(fp.amount),
            "payment_mode": _val(fp.payment_mode),
            "reference_number": _val(fp.reference_number),
        }
        for fp, sfa, stu, fs in records
    ]
    return _csv_response(rows, "fee_payments_export.csv")


@router.get("/exam-results", summary="Export Exam Results as CSV")
def export_exam_results(
    exam_id: UUID | None = Query(default=None),
    current_user: IdentityUser = Depends(require_permission("marks.view")),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    from sqlalchemy import select
    from app.models.exam.student_exam_result import StudentExamResult
    from app.models.exam.exam_schedule import ExamSchedule
    from app.models.exam.exam import Exam
    from app.models.student.student import Student
    from app.models.subject.subject import Subject

    q = (
        select(StudentExamResult, ExamSchedule, Exam, Student, Subject)
        .join(ExamSchedule, StudentExamResult.exam_schedule_id == ExamSchedule.id)
        .join(Exam, ExamSchedule.exam_id == Exam.id)
        .join(Student, StudentExamResult.student_id == Student.id)
        .join(Subject, ExamSchedule.subject_id == Subject.id)
        .where(
            Exam.school_id == current_user.school_id,
            StudentExamResult.is_deleted.is_(False),
        )
    )
    if exam_id:
        q = q.where(Exam.id == exam_id)
    q = q.order_by(Exam.name, Subject.subject_name, Student.admission_number)
    records = db.execute(q).all()

    rows = [
        {
            "exam_name": _val(ex.name),
            "subject": _val(sub.subject_name),
            "student_name": f"{stu.first_name} {stu.last_name}",
            "admission_number": _val(stu.admission_number),
            "roll_number": _val(stu.roll_number),
            "marks_obtained": _val(res.marks_obtained),
            "max_marks": _val(sched.maximum_marks),
        }
        for res, sched, ex, stu, sub in records
    ]
    exam_headers = ["exam_name", "subject", "student_name", "admission_number",
                    "roll_number", "marks_obtained", "max_marks"]
    return _csv_response(rows, "exam_results_export.csv", headers_schema=exam_headers)
