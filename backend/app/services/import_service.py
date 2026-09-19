"""
Data Import & Legacy Migration Service — Phase 30.9
Supports CSV/XLSX import for:
1. Students
2. Teachers
3. Parents
4. Fee Structures
5. Outstanding Balances (Opening Balances without fake payment generation)
6. Historical Marks / Results

Includes schema validation, reference resolution, dry-run preview, and transactional commit.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime, time as dt_time
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums.exam import (
    AssessmentType,
    AttemptType,
    ExamStatus,
)
from app.common.enums.fees import (
    FeeCategory,
    FeeStructureStatus,
    StudentFeeAssignmentStatus,
)
from app.common.enums.student import Gender, StudentStatus
from app.common.logger.logger import get_logger

logger = get_logger(__name__)

TODAY = datetime.now().date()


# ── Column Schemas ─────────────────────────────────────────────────────────────

STUDENT_REQUIRED_COLUMNS = {"first_name", "last_name", "gender", "admission_number"}
STUDENT_OPTIONAL_COLUMNS = {
    "middle_name", "roll_number", "date_of_birth", "admission_date",
    "blood_group", "phone", "email",
    "address_line1", "city", "district", "state", "country", "postal_code",
    "class_name", "section_name", "academic_year_name",
    "parent_phone", "parent_name",
}

TEACHER_REQUIRED_COLUMNS = {"first_name", "last_name"}
TEACHER_OPTIONAL_COLUMNS = {
    "middle_name", "employee_id", "phone", "email", "gender",
    "date_of_birth", "qualification", "specialization", "joining_date",
    "experience_years", "address_line1", "city", "state",
}

PARENT_REQUIRED_COLUMNS = {"primary_phone"}
PARENT_OPTIONAL_COLUMNS = {
    "father_name", "mother_name", "guardian_name", "relationship",
    "secondary_phone", "email", "occupation", "annual_income",
    "address_line1", "city", "district", "state",
}

FEE_STRUCTURE_REQUIRED_COLUMNS = {"academic_year", "fee_structure_name", "item_name", "amount"}
FEE_STRUCTURE_OPTIONAL_COLUMNS = {"class_name", "item_category", "is_optional", "description"}

OUTSTANDING_BALANCE_REQUIRED_COLUMNS = {"admission_number", "academic_year", "fee_name", "assessed_amount"}
OUTSTANDING_BALANCE_OPTIONAL_COLUMNS = {"paid_amount", "due_date", "remarks"}

HISTORICAL_MARKS_REQUIRED_COLUMNS = {
    "admission_number", "academic_year", "class_name", "section_name",
    "exam_name", "subject_code", "marks_obtained"
}
HISTORICAL_MARKS_OPTIONAL_COLUMNS = {"max_marks", "passing_marks", "remarks"}

ENTITY_SCHEMAS = {
    "students": {
        "required": STUDENT_REQUIRED_COLUMNS,
        "optional": STUDENT_OPTIONAL_COLUMNS,
        "description": (
            "Required: first_name, last_name, gender, admission_number. "
            "Optional: class_name, section_name, academic_year_name, parent_phone, parent_name, ..."
        ),
    },
    "teachers": {
        "required": TEACHER_REQUIRED_COLUMNS,
        "optional": TEACHER_OPTIONAL_COLUMNS,
        "description": "Required: first_name, last_name. Optional: email, phone, employee_id, ...",
    },
    "parents": {
        "required": PARENT_REQUIRED_COLUMNS,
        "optional": PARENT_OPTIONAL_COLUMNS,
        "description": "Required: primary_phone. Optional: father_name, mother_name, email, ...",
    },
    "fee_structures": {
        "required": FEE_STRUCTURE_REQUIRED_COLUMNS,
        "optional": FEE_STRUCTURE_OPTIONAL_COLUMNS,
        "description": (
            "Required: academic_year, fee_structure_name, item_name, amount. "
            "Optional: class_name, item_category (TUITION, TRANSPORT, HOSTEL, EXAMINATION, MISCELLANEOUS), is_optional, description"
        ),
    },
    "outstanding_balances": {
        "required": OUTSTANDING_BALANCE_REQUIRED_COLUMNS,
        "optional": OUTSTANDING_BALANCE_OPTIONAL_COLUMNS,
        "description": (
            "Required: admission_number, academic_year, fee_name, assessed_amount. "
            "Optional: paid_amount, due_date, remarks. "
            "Note: Sets opening student balances without generating fake payment transactions."
        ),
    },
    "historical_marks": {
        "required": HISTORICAL_MARKS_REQUIRED_COLUMNS,
        "optional": HISTORICAL_MARKS_OPTIONAL_COLUMNS,
        "description": (
            "Required: admission_number, academic_year, class_name, section_name, exam_name, subject_code, marks_obtained. "
            "Optional: max_marks (default 100), passing_marks (default 35), remarks"
        ),
    },
}


# ── Result Types ───────────────────────────────────────────────────────────────

@dataclass
class RowError:
    row_number: int
    field: str | None
    message: str


@dataclass
class ImportResult:
    entity_type: str
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    errors: list[RowError] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "entity_type": self.entity_type,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "duplicate_rows": self.duplicate_rows,
            "inserted_rows": self.inserted_rows,
            "updated_rows": self.updated_rows,
            "skipped_rows": self.skipped_rows,
            "errors": [
                {"row_number": e.row_number, "field": e.field, "message": e.message}
                for e in self.errors
            ],
        }


# ── File Parsing ───────────────────────────────────────────────────────────────

def parse_csv_bytes(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig").strip()
    if not text:
        return []
    reader = csv.DictReader(io.StringIO(text))
    return [{k.strip().lower(): (v.strip() if v else "") for k, v in row.items()} for row in reader]


def parse_xlsx_bytes(content: bytes) -> list[dict[str, str]] | None:
    try:
        import openpyxl  # type: ignore
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h).strip().lower() if h is not None else "" for h in next(rows_iter, [])]
        result = []
        for row in rows_iter:
            if all(v is None for v in row):
                continue
            result.append({headers[i]: (str(v).strip() if v is not None else "") for i, v in enumerate(row)})
        return result
    except ImportError:
        return None


# ── Helpers & Parsers ──────────────────────────────────────────────────────────

def validate_row(row: dict, row_number: int, required: set[str]) -> list[RowError]:
    return [
        RowError(row_number=row_number, field=col, message=f"Required field '{col}' is empty")
        for col in required if not row.get(col, "").strip()
    ]


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _safe_int(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except (ValueError, TypeError):
        return None


def _safe_float(value: str | None) -> float | None:
    try:
        return float(value) if value else None
    except (ValueError, TypeError):
        return None


def _safe_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    clean = str(value).strip().replace("$", "").replace("₹", "").replace(",", "")
    try:
        dec = Decimal(clean)
        if dec.is_nan() or dec.is_infinite():
            return None
        return dec
    except (InvalidOperation, TypeError, ValueError):
        return None


def _s(value: str | None, default: str = "N/A") -> str:
    """Return value or a default non-empty string for NOT NULL fields."""
    v = (value or "").strip()
    return v if v else default


# ── Entity Resolvers ───────────────────────────────────────────────────────────

def _get_current_academic_year(db: Session, school_id: UUID):
    from app.models.academic_year.academic_year import AcademicYear
    return db.execute(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
            AcademicYear.is_deleted.is_(False),
        )
    ).scalar_one_or_none()


def _get_academic_year_by_name(db: Session, school_id: UUID, name: str):
    from app.models.academic_year.academic_year import AcademicYear
    return db.execute(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            func.lower(AcademicYear.name) == name.lower(),
            AcademicYear.is_deleted.is_(False),
        )
    ).scalar_one_or_none()


def _get_student_by_admission_number(db: Session, school_id: UUID, admission_number: str):
    from app.models.student.student import Student
    return db.execute(
        select(Student).where(
            Student.school_id == school_id,
            func.lower(Student.admission_number) == admission_number.lower(),
            Student.is_deleted.is_(False),
        )
    ).scalar_one_or_none()


def _get_or_create_class(db: Session, school_id: UUID, name: str | None):
    from app.models.school_class.school_class import SchoolClass
    c_name = name.strip() if name else "General"
    existing = db.execute(
        select(SchoolClass).where(
            SchoolClass.school_id == school_id,
            func.lower(SchoolClass.name) == c_name.lower(),
            SchoolClass.is_deleted.is_(False),
        )
    ).scalars().first()
    if existing:
        return existing
    new_class = SchoolClass(
        school_id=school_id,
        name=c_name,
        display_order=1,
    )
    db.add(new_class)
    db.flush()
    return new_class


def _get_or_create_section(db: Session, school_class_id: UUID, name: str | None):
    from app.models.section.section import Section
    s_name = name.strip() if name else "A"
    existing = db.execute(
        select(Section).where(
            Section.school_class_id == school_class_id,
            func.lower(Section.name) == s_name.lower(),
            Section.is_deleted.is_(False),
        )
    ).scalars().first()
    if existing:
        return existing
    new_sec = Section(
        school_class_id=school_class_id,
        name=s_name,
    )
    db.add(new_sec)
    db.flush()
    return new_sec


def _get_or_create_parent(db: Session, school_id: UUID, phone: str | None, name: str | None):
    from app.models.parent.parent import Parent
    p_phone = phone.strip() if phone else f"90000{str(school_id)[:5]}"
    existing = db.execute(
        select(Parent).where(
            Parent.school_id == school_id,
            func.lower(Parent.primary_phone) == p_phone.lower(),
            Parent.is_deleted.is_(False),
        )
    ).scalars().first()
    if existing:
        return existing
    p_name = name.strip() if name else "Parent/Guardian"
    parent = Parent(
        school_id=school_id,
        father_name=p_name,
        guardian_name=p_name,
        relationship="FATHER",
        primary_phone=p_phone,
        address_line1="N/A",
        city="N/A",
        district="N/A",
        state="N/A",
        country="India",
        postal_code="000000",
    )
    db.add(parent)
    db.flush()
    return parent


def _get_or_create_subject(db: Session, school_id: UUID, code: str, name: str | None = None):
    from app.models.subject.subject import Subject
    clean_code = code.strip().upper()
    existing = db.execute(
        select(Subject).where(
            Subject.school_id == school_id,
            func.lower(Subject.subject_code) == clean_code.lower(),
            Subject.is_deleted.is_(False),
        )
    ).scalars().first()
    if existing:
        return existing
    new_sub = Subject(
        school_id=school_id,
        subject_code=clean_code,
        subject_name=name.strip() if name else clean_code,
    )
    db.add(new_sub)
    db.flush()
    return new_sub


def _get_or_create_exam(db: Session, school_id: UUID, academic_year_id: UUID, exam_name: str):
    from app.models.exam.exam import Exam
    clean_name = exam_name.strip()
    existing = db.execute(
        select(Exam).where(
            Exam.school_id == school_id,
            Exam.academic_year_id == academic_year_id,
            func.lower(Exam.name) == clean_name.lower(),
            Exam.is_deleted.is_(False),
        )
    ).scalars().first()
    if existing:
        return existing
    new_exam = Exam(
        school_id=school_id,
        academic_year_id=academic_year_id,
        name=clean_name,
        assessment_type=AssessmentType.SUMMATIVE_ASSESSMENT,
        attempt_type=AttemptType.REGULAR,
        status=ExamStatus.COMPLETED,
        start_date=TODAY,
        end_date=TODAY,
    )
    db.add(new_exam)
    db.flush()
    return new_exam


def _get_or_create_exam_schedule(
    db: Session,
    school_id: UUID,
    exam_id: UUID,
    academic_year_id: UUID,
    school_class_id: UUID,
    section_id: UUID,
    subject_id: UUID,
    maximum_marks: Decimal,
    passing_marks: Decimal,
):
    from app.models.exam.exam_schedule import ExamSchedule
    existing = db.execute(
        select(ExamSchedule).where(
            ExamSchedule.exam_id == exam_id,
            ExamSchedule.section_id == section_id,
            ExamSchedule.subject_id == subject_id,
            ExamSchedule.is_deleted.is_(False),
        )
    ).scalars().first()
    if existing:
        return existing
    new_sched = ExamSchedule(
        exam_id=exam_id,
        school_id=school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        subject_id=subject_id,
        exam_date=TODAY,
        start_time=dt_time(9, 0),
        end_time=dt_time(12, 0),
        maximum_marks=maximum_marks,
        passing_marks=passing_marks,
    )
    db.add(new_sched)
    db.flush()
    return new_sched


def _get_or_create_fee_structure(
    db: Session,
    school_id: UUID,
    academic_year_id: UUID,
    school_class_id: UUID | None,
    name: str,
    description: str | None = None,
):
    from app.models.fees.fee_structure import FeeStructure
    clean_name = name.strip()
    query = select(FeeStructure).where(
        FeeStructure.school_id == school_id,
        FeeStructure.academic_year_id == academic_year_id,
        func.lower(FeeStructure.name) == clean_name.lower(),
        FeeStructure.is_deleted.is_(False),
    )
    if school_class_id:
        query = query.where(FeeStructure.school_class_id == school_class_id)
    else:
        query = query.where(FeeStructure.school_class_id.is_(None))

    existing = db.execute(query).scalars().first()
    if existing:
        return existing

    new_struct = FeeStructure(
        school_id=school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        name=clean_name,
        description=description or "Legacy Migrated Fee Structure",
        status=FeeStructureStatus.ACTIVE,
    )
    db.add(new_struct)
    db.flush()
    return new_struct


# ── Domain Import Handlers ─────────────────────────────────────────────────────

def _import_students(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from app.models.student.student import Student

    valid_genders = {g.value for g in Gender}

    for i, row in enumerate(rows, start=2):
        result.total_rows += 1
        errors = validate_row(row, i, STUDENT_REQUIRED_COLUMNS)

        gender_val = row.get("gender", "").strip().upper()
        if gender_val not in valid_genders:
            errors.append(RowError(i, "gender", f"Invalid gender '{gender_val}'. Valid: {sorted(valid_genders)}"))

        if errors:
            result.invalid_rows += 1
            result.errors.extend(errors)
            continue

        admission_number = row.get("admission_number", "").strip()
        if admission_number:
            dup = db.execute(
                select(Student).where(
                    Student.school_id == school_id,
                    func.lower(Student.admission_number) == admission_number.lower(),
                    Student.is_deleted.is_(False),
                )
            ).scalar_one_or_none()
            if dup:
                result.duplicate_rows += 1
                result.skipped_rows += 1
                result.errors.append(RowError(i, "admission_number", f"'{admission_number}' already exists — skipped"))
                continue

        ay_name = row.get("academic_year_name", "").strip()
        academic_year = _get_academic_year_by_name(db, school_id, ay_name) if ay_name else _get_current_academic_year(db, school_id)
        if not academic_year:
            result.skipped_rows += 1
            result.errors.append(RowError(i, "academic_year", "No active academic year found."))
            result.invalid_rows += 1
            continue

        class_name = row.get("class_name", "").strip()
        section_name = row.get("section_name", "").strip()
        parent_phone = row.get("parent_phone", "").strip()
        parent_name = row.get("parent_name", "").strip()

        school_class = _get_or_create_class(db, school_id, class_name)
        section = _get_or_create_section(db, school_class.id, section_name)
        parent = _get_or_create_parent(db, school_id, parent_phone, parent_name)

        roll_number = row.get("roll_number", "").strip() or admission_number

        result.valid_rows += 1
        student = Student(
            school_id=school_id,
            first_name=row["first_name"],
            last_name=row["last_name"],
            middle_name=row.get("middle_name") or None,
            gender=gender_val,
            date_of_birth=_parse_date(row.get("date_of_birth")) or TODAY,
            admission_number=admission_number,
            roll_number=roll_number,
            admission_date=_parse_date(row.get("admission_date")) or TODAY,
            blood_group=row.get("blood_group") or None,
            phone=row.get("phone") or None,
            email=row.get("email") or None,
            address_line1=_s(row.get("address_line1")),
            city=_s(row.get("city")),
            district=_s(row.get("district")),
            state=_s(row.get("state")),
            country=_s(row.get("country"), "India"),
            postal_code=_s(row.get("postal_code"), "000000"),
            status=StudentStatus.ACTIVE,
            academic_year_id=academic_year.id,
            school_class_id=school_class.id,
            section_id=section.id,
            parent_id=parent.id,
        )
        db.add(student)
        result.inserted_rows += 1


def _import_teachers(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from app.models.teacher.teacher import Teacher

    for i, row in enumerate(rows, start=2):
        result.total_rows += 1
        errors = validate_row(row, i, TEACHER_REQUIRED_COLUMNS)
        if errors:
            result.invalid_rows += 1
            result.errors.extend(errors)
            continue

        email = row.get("email", "").strip() or None
        emp_id = row.get("employee_id", "").strip() or None

        if email:
            dup = db.execute(
                select(Teacher).where(
                    Teacher.school_id == school_id,
                    func.lower(Teacher.email) == email.lower(),
                    Teacher.is_deleted.is_(False),
                )
            ).scalar_one_or_none()
            if dup:
                result.duplicate_rows += 1
                result.skipped_rows += 1
                result.errors.append(RowError(i, "email", f"Email '{email}' already exists — skipped"))
                continue

        result.valid_rows += 1
        teacher = Teacher(
            school_id=school_id,
            first_name=row["first_name"],
            last_name=row["last_name"],
            middle_name=row.get("middle_name") or None,
            employee_id=emp_id,
            phone=row.get("phone") or None,
            email=email,
            gender=row.get("gender", "").strip().upper() or "MALE",
            date_of_birth=_parse_date(row.get("date_of_birth")) or date(1990, 1, 1),
            joining_date=_parse_date(row.get("joining_date")) or TODAY,
            qualification=row.get("qualification") or "B.Ed",
            specialization=row.get("specialization") or None,
            experience_years=_safe_int(row.get("experience_years")),
            address_line1=_s(row.get("address_line1")),
            city=_s(row.get("city")),
            district=_s(row.get("district")),
            state=_s(row.get("state")),
            country=_s(row.get("country"), "India"),
            postal_code=_s(row.get("postal_code"), "000000"),
        )
        db.add(teacher)
        result.inserted_rows += 1


def _import_parents(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from app.models.parent.parent import Parent

    for i, row in enumerate(rows, start=2):
        result.total_rows += 1
        errors = validate_row(row, i, PARENT_REQUIRED_COLUMNS)
        if errors:
            result.invalid_rows += 1
            result.errors.extend(errors)
            continue

        phone = row.get("primary_phone", "").strip()
        dup = db.execute(
            select(Parent).where(
                Parent.school_id == school_id,
                func.lower(Parent.primary_phone) == phone.lower(),
                Parent.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if dup:
            result.duplicate_rows += 1
            result.skipped_rows += 1
            result.errors.append(RowError(i, "primary_phone", f"Phone '{phone}' already exists — skipped"))
            continue

        result.valid_rows += 1
        parent = Parent(
            school_id=school_id,
            father_name=_s(row.get("father_name"), "Parent/Guardian"),
            mother_name=row.get("mother_name") or None,
            guardian_name=_s(row.get("guardian_name"), "Parent/Guardian"),
            relationship=_s(row.get("relationship"), "FATHER"),
            primary_phone=phone,
            secondary_phone=row.get("secondary_phone") or None,
            email=row.get("email") or None,
            occupation=row.get("occupation") or None,
            annual_income=_safe_float(row.get("annual_income")),
            address_line1=_s(row.get("address_line1")),
            city=_s(row.get("city")),
            district=_s(row.get("district")),
            state=_s(row.get("state")),
            country=_s(row.get("country"), "India"),
            postal_code=_s(row.get("postal_code"), "000000"),
        )
        db.add(parent)
        result.inserted_rows += 1


def _import_fee_structures(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from app.models.fees.fee_structure import FeeItem

    valid_categories = {c.value for c in FeeCategory}

    for i, row in enumerate(rows, start=2):
        result.total_rows += 1
        errors = validate_row(row, i, FEE_STRUCTURE_REQUIRED_COLUMNS)
        if errors:
            result.invalid_rows += 1
            result.errors.extend(errors)
            continue

        # Resolve Academic Year
        ay_str = row.get("academic_year", "").strip()
        academic_year = _get_academic_year_by_name(db, school_id, ay_str) or _get_current_academic_year(db, school_id)
        if not academic_year:
            result.invalid_rows += 1
            result.errors.append(RowError(i, "academic_year", f"Academic year '{ay_str}' not found"))
            continue

        # Amount parsing
        amount_dec = _safe_decimal(row.get("amount"))
        if amount_dec is None or amount_dec < Decimal("0"):
            result.invalid_rows += 1
            result.errors.append(RowError(i, "amount", f"Invalid monetary amount: '{row.get('amount')}'"))
            continue

        # Category parsing
        cat_str = row.get("item_category", "").strip().upper() or "TUITION"
        if cat_str not in valid_categories:
            result.invalid_rows += 1
            result.errors.append(RowError(i, "item_category", f"Invalid fee category '{cat_str}'. Valid: {sorted(valid_categories)}"))
            continue

        # Class resolution
        c_name = row.get("class_name", "").strip()
        school_class = _get_or_create_class(db, school_id, c_name) if c_name else None
        class_id = school_class.id if school_class else None

        struct_name = row.get("fee_structure_name", "").strip()
        item_name = row.get("item_name", "").strip()
        is_optional = row.get("is_optional", "").strip().lower() in ("true", "1", "yes")
        desc = row.get("description", "").strip() or None

        fee_struct = _get_or_create_fee_structure(db, school_id, academic_year.id, class_id, struct_name, desc)

        # Check existing item inside structure
        existing_item = db.execute(
            select(FeeItem).where(
                FeeItem.fee_structure_id == fee_struct.id,
                func.lower(FeeItem.name) == item_name.lower(),
                FeeItem.is_deleted.is_(False),
            )
        ).scalars().first()

        result.valid_rows += 1
        if existing_item:
            existing_item.amount = amount_dec
            existing_item.category = FeeCategory(cat_str)
            existing_item.is_optional = is_optional
            result.updated_rows += 1
        else:
            new_item = FeeItem(
                fee_structure_id=fee_struct.id,
                name=item_name,
                category=FeeCategory(cat_str),
                amount=amount_dec,
                is_optional=is_optional,
            )
            db.add(new_item)
            result.inserted_rows += 1


def _import_outstanding_balances(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from app.models.fees.student_fee_assignment import (
        StudentFeeAssignment,
        StudentFeeItem,
    )

    for i, row in enumerate(rows, start=2):
        result.total_rows += 1
        errors = validate_row(row, i, OUTSTANDING_BALANCE_REQUIRED_COLUMNS)
        if errors:
            result.invalid_rows += 1
            result.errors.extend(errors)
            continue

        adm_num = row.get("admission_number", "").strip()
        student = _get_student_by_admission_number(db, school_id, adm_num)
        if not student:
            result.invalid_rows += 1
            result.errors.append(RowError(i, "admission_number", f"Student with admission number '{adm_num}' not found"))
            continue

        ay_str = row.get("academic_year", "").strip()
        academic_year = _get_academic_year_by_name(db, school_id, ay_str) or _get_current_academic_year(db, school_id)
        if not academic_year:
            result.invalid_rows += 1
            result.errors.append(RowError(i, "academic_year", f"Academic year '{ay_str}' not found"))
            continue

        assessed_dec = _safe_decimal(row.get("assessed_amount"))
        if assessed_dec is None or assessed_dec < Decimal("0"):
            result.invalid_rows += 1
            result.errors.append(RowError(i, "assessed_amount", f"Invalid assessed amount '{row.get('assessed_amount')}'"))
            continue

        paid_dec = _safe_decimal(row.get("paid_amount")) or Decimal("0.00")
        if paid_dec < Decimal("0") or paid_dec > assessed_dec:
            result.invalid_rows += 1
            result.errors.append(
                RowError(i, "paid_amount", f"Paid amount ({paid_dec}) must be between 0 and assessed amount ({assessed_dec})")
            )
            continue

        due_date = _parse_date(row.get("due_date")) or TODAY
        fee_name = row.get("fee_name", "").strip()
        remarks = row.get("remarks", "").strip() or "Legacy Migrated Opening Balance"

        # Resolve or create opening fee structure
        struct_name = f"Legacy Balances - {academic_year.name}"
        fee_struct = _get_or_create_fee_structure(db, school_id, academic_year.id, student.school_class_id, struct_name)

        # Status determination:
        # PENDING: paid_amount == 0 (100% outstanding)
        # PARTIALLY_PAID: 0 < paid_amount < assessed_amount
        # PAID: paid_amount == assessed_amount (0 outstanding)
        if paid_dec == Decimal("0.00"):
            assign_status = StudentFeeAssignmentStatus.PENDING
        elif paid_dec < assessed_dec:
            assign_status = StudentFeeAssignmentStatus.PARTIALLY_PAID
        else:
            assign_status = StudentFeeAssignmentStatus.PAID

        # Find or create StudentFeeAssignment
        assignment = db.execute(
            select(StudentFeeAssignment).where(
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.academic_year_id == academic_year.id,
                StudentFeeAssignment.student_id == student.id,
                StudentFeeAssignment.fee_structure_id == fee_struct.id,
                StudentFeeAssignment.is_deleted.is_(False),
            )
        ).scalars().first()

        result.valid_rows += 1
        if not assignment:
            assignment = StudentFeeAssignment(
                school_id=school_id,
                academic_year_id=academic_year.id,
                student_id=student.id,
                fee_structure_id=fee_struct.id,
                status=assign_status,
                due_date=due_date,
                remarks=remarks,
            )
            db.add(assignment)
            db.flush()
            result.inserted_rows += 1
        else:
            assignment.status = assign_status
            assignment.due_date = due_date
            assignment.remarks = remarks
            result.updated_rows += 1

        # Find or create StudentFeeItem
        fee_item = db.execute(
            select(StudentFeeItem).where(
                StudentFeeItem.student_fee_assignment_id == assignment.id,
                func.lower(StudentFeeItem.name) == fee_name.lower(),
                StudentFeeItem.is_deleted.is_(False),
            )
        ).scalars().first()

        if fee_item:
            fee_item.amount = assessed_dec
        else:
            new_student_item = StudentFeeItem(
                student_fee_assignment_id=assignment.id,
                name=fee_name,
                category=FeeCategory.MISCELLANEOUS,
                amount=assessed_dec,
                is_optional=False,
                is_applicable=True,
            )
            db.add(new_student_item)


def _import_historical_marks(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from app.models.exam.student_exam_result import StudentExamResult

    for i, row in enumerate(rows, start=2):
        result.total_rows += 1
        errors = validate_row(row, i, HISTORICAL_MARKS_REQUIRED_COLUMNS)
        if errors:
            result.invalid_rows += 1
            result.errors.extend(errors)
            continue

        adm_num = row.get("admission_number", "").strip()
        student = _get_student_by_admission_number(db, school_id, adm_num)
        if not student:
            result.invalid_rows += 1
            result.errors.append(RowError(i, "admission_number", f"Student '{adm_num}' not found"))
            continue

        ay_str = row.get("academic_year", "").strip()
        academic_year = _get_academic_year_by_name(db, school_id, ay_str) or _get_current_academic_year(db, school_id)
        if not academic_year:
            result.invalid_rows += 1
            result.errors.append(RowError(i, "academic_year", f"Academic year '{ay_str}' not found"))
            continue

        c_name = row.get("class_name", "").strip()
        s_name = row.get("section_name", "").strip()
        school_class = _get_or_create_class(db, school_id, c_name)
        section = _get_or_create_section(db, school_class.id, s_name)

        sub_code = row.get("subject_code", "").strip()
        subject = _get_or_create_subject(db, school_id, sub_code)

        exam_name = row.get("exam_name", "").strip()
        exam = _get_or_create_exam(db, school_id, academic_year.id, exam_name)

        max_marks = _safe_decimal(row.get("max_marks")) or Decimal("100.00")
        passing_marks = _safe_decimal(row.get("passing_marks")) or Decimal("35.00")

        marks_obtained = _safe_decimal(row.get("marks_obtained"))
        if marks_obtained is None or marks_obtained < Decimal("0"):
            result.invalid_rows += 1
            result.errors.append(RowError(i, "marks_obtained", f"Invalid marks obtained: '{row.get('marks_obtained')}'"))
            continue

        if marks_obtained > max_marks:
            result.invalid_rows += 1
            result.errors.append(RowError(i, "marks_obtained", f"Marks obtained ({marks_obtained}) exceeds max marks ({max_marks})"))
            continue

        remarks = row.get("remarks", "").strip() or None

        # Resolve ExamSchedule
        schedule = _get_or_create_exam_schedule(
            db, school_id, exam.id, academic_year.id, school_class.id, section.id, subject.id, max_marks, passing_marks
        )

        # Check existing result
        existing_result = db.execute(
            select(StudentExamResult).where(
                StudentExamResult.exam_schedule_id == schedule.id,
                StudentExamResult.student_id == student.id,
                StudentExamResult.is_deleted.is_(False),
            )
        ).scalars().first()

        result.valid_rows += 1
        if existing_result:
            existing_result.marks_obtained = marks_obtained
            existing_result.remarks = remarks
            result.updated_rows += 1
        else:
            new_res = StudentExamResult(
                exam_schedule_id=schedule.id,
                student_id=student.id,
                marks_obtained=marks_obtained,
                remarks=remarks,
            )
            db.add(new_res)
            result.inserted_rows += 1


# ── Main Import Entry ──────────────────────────────────────────────────────────

IMPORT_HANDLERS = {
    "students": _import_students,
    "teachers": _import_teachers,
    "parents": _import_parents,
    "fee_structures": _import_fee_structures,
    "outstanding_balances": _import_outstanding_balances,
    "historical_marks": _import_historical_marks,
}


def import_data(
    db: Session,
    entity_type: str,
    file_content: bytes,
    filename: str,
    school_id: UUID,
) -> ImportResult:
    """
    Parse and import CSV/XLSX data for any supported entity type.
    """
    result = ImportResult(entity_type=entity_type)

    if entity_type not in ENTITY_SCHEMAS:
        raise ValueError(f"Unsupported entity type: '{entity_type}'. Valid: {list(ENTITY_SCHEMAS)}")

    fname_lower = filename.lower()
    if fname_lower.endswith((".xlsx", ".xls")):
        rows = parse_xlsx_bytes(file_content)
        if rows is None:
            result.errors.append(RowError(0, None, "XLSX unavailable — openpyxl not installed. Use CSV."))
            return result
    elif fname_lower.endswith(".csv"):
        rows = parse_csv_bytes(file_content)
    else:
        result.errors.append(RowError(0, None, "Unsupported format. Upload .csv or .xlsx"))
        return result

    if not rows:
        result.errors.append(RowError(0, None, "File is empty or has no data rows"))
        return result

    schema = ENTITY_SCHEMAS[entity_type]
    actual_cols = set(rows[0].keys())
    missing = schema["required"] - actual_cols
    if missing:
        result.errors.append(RowError(0, None,
            f"Missing required columns: {sorted(missing)}. "
            f"Schema hint: {schema['description']}"))
        return result

    handler = IMPORT_HANDLERS[entity_type]
    try:
        handler(db, rows, school_id, result)
        db.flush()
    except Exception as exc:
        logger.exception("Import fatal error for %s: %s", entity_type, exc)
        try:
            db.rollback()
        except Exception:
            pass
        result.errors.append(RowError(0, None, f"Fatal error — all changes rolled back: {exc}"))

    return result


def preview_import(
    db: Session,
    entity_type: str,
    file_content: bytes,
    filename: str,
    school_id: UUID,
) -> dict:
    """
    Dry-run validation for any entity type.
    Performs ZERO persistent database mutations.
    """
    if entity_type not in ENTITY_SCHEMAS:
        return {
            "entity_type": entity_type,
            "total_rows": 0,
            "valid_rows_count": 0,
            "invalid_rows_count": 1,
            "warning_rows_count": 0,
            "duplicate_candidates": [],
            "invalid_references": [f"Unsupported entity type '{entity_type}'"],
            "can_commit": False,
            "rows_preview": [],
        }

    fname_lower = filename.lower()
    if fname_lower.endswith((".xlsx", ".xls")):
        rows = parse_xlsx_bytes(file_content)
    elif fname_lower.endswith(".csv"):
        rows = parse_csv_bytes(file_content)
    else:
        return {
            "entity_type": entity_type,
            "total_rows": 0,
            "valid_rows_count": 0,
            "invalid_rows_count": 1,
            "warning_rows_count": 0,
            "duplicate_candidates": [],
            "invalid_references": [],
            "can_commit": False,
            "rows_preview": [
                {
                    "row_number": 0,
                    "status": "BLOCKING_ERROR",
                    "errors": ["Unsupported format. Upload .csv or .xlsx"],
                    "warnings": [],
                }
            ],
        }

    if not rows:
        return {
            "entity_type": entity_type,
            "total_rows": 0,
            "valid_rows_count": 0,
            "invalid_rows_count": 1,
            "warning_rows_count": 0,
            "duplicate_candidates": [],
            "invalid_references": [],
            "can_commit": False,
            "rows_preview": [
                {
                    "row_number": 0,
                    "status": "BLOCKING_ERROR",
                    "errors": ["File is empty or has no data rows"],
                    "warnings": [],
                }
            ],
        }

    schema = ENTITY_SCHEMAS[entity_type]
    actual_cols = set(rows[0].keys())
    missing = schema["required"] - actual_cols
    if missing:
        return {
            "entity_type": entity_type,
            "total_rows": len(rows),
            "valid_rows_count": 0,
            "invalid_rows_count": len(rows),
            "warning_rows_count": 0,
            "duplicate_candidates": [],
            "invalid_references": [f"Missing required columns: {sorted(missing)}"],
            "can_commit": False,
            "rows_preview": [],
        }

    # Run handler inside a transaction savepoint that is unconditionally rolled back
    savepoint = db.begin_nested()
    result = ImportResult(entity_type=entity_type)
    try:
        handler = IMPORT_HANDLERS[entity_type]
        handler(db, rows, school_id, result)
    finally:
        # Guarantee ZERO persistent mutations during preview
        savepoint.rollback()

    rows_preview = []
    errors_list = []
    for e in result.errors:
        rows_preview.append({
            "row_number": e.row_number,
            "field": e.field,
            "status": "BLOCKING_ERROR",
            "errors": [e.message],
            "warnings": [],
        })
        errors_list.append({
            "row_number": e.row_number,
            "field": e.field,
            "message": e.message,
        })

    ref_errors = sum(1 for e in result.errors if "not found" in e.message.lower() or "reference" in e.message.lower())

    return {
        "entity_type": entity_type,
        "filename": filename,
        "total_rows": result.total_rows,
        "valid_rows": result.valid_rows,
        "invalid_rows": result.invalid_rows,
        "duplicate_candidates": result.duplicate_rows,
        "reference_errors": ref_errors,
        "valid_rows_count": result.valid_rows,
        "invalid_rows_count": result.invalid_rows,
        "warning_rows_count": 0,
        "inserted_estimate": result.inserted_rows,
        "updated_estimate": result.updated_rows,
        "skipped_estimate": result.skipped_rows,
        "can_commit": (result.invalid_rows == 0 and result.total_rows > 0),
        "errors": errors_list,
        "duplicates": [],
        "preview_rows": (rows or [])[:10],
        "rows_preview": rows_preview,
    }


def commit_import(
    db: Session,
    entity_type: str,
    file_content: bytes,
    filename: str,
    school_id: UUID,
    atomic_mode: bool = True,
) -> dict:
    """
    Execute transactional commit of validated import data.
    Rolls back completely on failure if atomic_mode=True.
    """
    preview = preview_import(db, entity_type, file_content, filename, school_id)

    if atomic_mode and not preview["can_commit"]:
        return {
            "success": False,
            "entity_type": entity_type,
            "filename": filename,
            "total_rows": preview["total_rows"],
            "committed_rows": 0,
            "inserted_rows": 0,
            "updated_rows": 0,
            "skipped_rows": preview["total_rows"],
            "failed_rows": preview["invalid_rows"],
            "message": f"Atomic commit failed: {preview['invalid_rows']} rows have validation errors. 0 records created.",
            "errors": preview["errors"],
        }

    savepoint = db.begin_nested()
    result = ImportResult(entity_type=entity_type)
    fname_lower = filename.lower()
    if fname_lower.endswith((".xlsx", ".xls")):
        rows = parse_xlsx_bytes(file_content)
    else:
        rows = parse_csv_bytes(file_content)

    try:
        handler = IMPORT_HANDLERS[entity_type]
        handler(db, rows or [], school_id, result)
        if atomic_mode and result.invalid_rows > 0:
            savepoint.rollback()
            return {
                "success": False,
                "entity_type": entity_type,
                "filename": filename,
                "total_rows": result.total_rows,
                "committed_rows": 0,
                "inserted_rows": 0,
                "updated_rows": 0,
                "skipped_rows": result.total_rows,
                "failed_rows": result.invalid_rows,
                "message": "Atomic import failed during database stage. All mutations rolled back.",
                "errors": [{"row_number": e.row_number, "field": e.field, "message": e.message} for e in result.errors],
            }
        db.commit()
    except Exception as exc:
        savepoint.rollback()
        logger.exception("Atomic import exception for %s: %s", entity_type, exc)
        return {
            "success": False,
            "entity_type": entity_type,
            "filename": filename,
            "total_rows": result.total_rows,
            "committed_rows": 0,
            "inserted_rows": 0,
            "updated_rows": 0,
            "skipped_rows": result.total_rows,
            "failed_rows": result.total_rows,
            "message": f"Fatal database error during import. All changes rolled back: {exc}",
            "errors": [{"row_number": 0, "field": None, "message": str(exc)}],
        }

    return {
        "success": True,
        "entity_type": entity_type,
        "filename": filename,
        "total_rows": result.total_rows,
        "committed_rows": result.inserted_rows + result.updated_rows,
        "inserted_rows": result.inserted_rows,
        "updated_rows": result.updated_rows,
        "skipped_rows": result.skipped_rows,
        "failed_rows": result.invalid_rows,
        "message": f"Successfully imported {result.inserted_rows} new records and updated {result.updated_rows} existing records.",
        "errors": [{"row_number": e.row_number, "field": e.field, "message": e.message} for e in result.errors],
    }


# Backwards compatibility aliases
preview_student_import = lambda db, file_content, filename, school_id: preview_import(db, "students", file_content, filename, school_id)
commit_student_import = lambda db, file_content, filename, school_id, atomic_mode=True: commit_import(db, "students", file_content, filename, school_id, atomic_mode=atomic_mode)
