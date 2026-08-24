"""
Data Import Service — Phase 9.1
Supports CSV/XLSX import for Students, Teachers, and Parents.
Verified empirically against actual model field constraints.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger

logger = get_logger(__name__)

TODAY = datetime.now().date()


# ── Column Schemas ─────────────────────────────────────────────────────────────

# Students: resolve class/section by name to get required FK IDs
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

ENTITY_SCHEMAS = {
    "students": {
        "required": STUDENT_REQUIRED_COLUMNS,
        "optional": STUDENT_OPTIONAL_COLUMNS,
        "description": (
            "Required: first_name, last_name, gender, admission_number. "
            "Optional: class_name, section_name, academic_year_name, "
            "parent_phone, parent_name, roll_number, date_of_birth, "
            "admission_date, phone, email, address_line1, city, district, "
            "state, country, postal_code"
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


# ── Helpers ────────────────────────────────────────────────────────────────────

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


def _s(value: str | None, default: str = "N/A") -> str:
    """Return value or a default non-empty string for NOT NULL fields."""
    v = (value or "").strip()
    return v if v else default


# ── School Lookup Helpers ──────────────────────────────────────────────────────

def _get_current_academic_year(db: Session, school_id: UUID):
    from sqlalchemy import select
    from app.models.academic_year.academic_year import AcademicYear
    return db.execute(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
            AcademicYear.is_deleted.is_(False),
        )
    ).scalar_one_or_none()


def _get_academic_year_by_name(db: Session, school_id: UUID, name: str):
    from sqlalchemy import select, func
    from app.models.academic_year.academic_year import AcademicYear
    return db.execute(
        select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            func.lower(AcademicYear.name) == name.lower(),
            AcademicYear.is_deleted.is_(False),
        )
    ).scalar_one_or_none()


def _get_or_create_class(db: Session, school_id: UUID, name: str | None):
    from sqlalchemy import select, func
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
    from sqlalchemy import select, func
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
    from sqlalchemy import select, func
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


# ── Import Handlers ────────────────────────────────────────────────────────────

def _import_students(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from sqlalchemy import select, func
    from app.models.student.student import Student
    from app.common.enums.student import Gender, StudentStatus

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

        # Resolve academic year
        ay_name = row.get("academic_year_name", "").strip()
        academic_year = None
        if ay_name:
            academic_year = _get_academic_year_by_name(db, school_id, ay_name)
        if not academic_year:
            academic_year = _get_current_academic_year(db, school_id)
        if not academic_year:
            result.skipped_rows += 1
            result.errors.append(RowError(i, "academic_year", "No active academic year found. Please set up an academic year first."))
            result.invalid_rows += 1
            continue

        # Resolve/create class, section, parent
        class_name = row.get("class_name", "").strip()
        section_name = row.get("section_name", "").strip()
        parent_phone = row.get("parent_phone", "").strip()
        parent_name = row.get("parent_name", "").strip()

        school_class = _get_or_create_class(db, school_id, class_name)
        section = _get_or_create_section(db, school_class.id, section_name)
        parent = _get_or_create_parent(db, school_id, parent_phone, parent_name)

        roll_number = row.get("roll_number", "").strip() or admission_number  # default roll to admission_number

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
    from sqlalchemy import select, func
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
            gender=row.get("gender", "").strip().upper() or None,
            date_of_birth=_parse_date(row.get("date_of_birth")),
            joining_date=_parse_date(row.get("joining_date")),
            qualification=row.get("qualification") or None,
            specialization=row.get("specialization") or None,
            experience_years=_safe_int(row.get("experience_years")),
            address_line1=row.get("address_line1") or None,
            city=row.get("city") or None,
            state=row.get("state") or None,
        )
        db.add(teacher)
        result.inserted_rows += 1


def _import_parents(db: Session, rows: list[dict], school_id: UUID, result: ImportResult) -> None:
    from sqlalchemy import select, func
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


# ── Main Import Entry ──────────────────────────────────────────────────────────

IMPORT_HANDLERS = {
    "students": _import_students,
    "teachers": _import_teachers,
    "parents": _import_parents,
}


def import_data(
    db: Session,
    entity_type: str,
    file_content: bytes,
    filename: str,
    school_id: UUID,
) -> ImportResult:
    """
    Parse and import CSV/XLSX data for the given entity type.
    Rolls back the session on fatal (non-per-row) errors.
    """
    result = ImportResult(entity_type=entity_type)

    if entity_type not in ENTITY_SCHEMAS:
        raise ValueError(f"Unsupported entity type: '{entity_type}'")

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


def preview_student_import(
    db: Session,
    file_content: bytes,
    filename: str,
    school_id: UUID,
) -> dict:
    from sqlalchemy import select, func
    from app.models.student.student import Student
    from app.common.enums.student import Gender

    fname_lower = filename.lower()
    if fname_lower.endswith((".xlsx", ".xls")):
        rows = parse_xlsx_bytes(file_content)
    elif fname_lower.endswith(".csv"):
        rows = parse_csv_bytes(file_content)
    else:
        return {
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
                    "admission_number": "",
                    "first_name": "",
                    "last_name": "",
                    "class_name": "",
                    "section_name": "",
                    "errors": ["Unsupported format. Upload .csv or .xlsx"],
                    "warnings": [],
                }
            ],
        }

    if not rows:
        return {
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
                    "admission_number": "",
                    "first_name": "",
                    "last_name": "",
                    "class_name": "",
                    "section_name": "",
                    "errors": ["File is empty or has no data rows"],
                    "warnings": [],
                }
            ],
        }

    schema = ENTITY_SCHEMAS["students"]
    actual_cols = set(rows[0].keys())
    missing = schema["required"] - actual_cols
    if missing:
        return {
            "total_rows": len(rows),
            "valid_rows_count": 0,
            "invalid_rows_count": len(rows),
            "warning_rows_count": 0,
            "duplicate_candidates": [],
            "invalid_references": [f"Missing required columns: {sorted(missing)}"],
            "can_commit": False,
            "rows_preview": [],
        }

    valid_genders = {g.value for g in Gender}
    seen_admissions = set()
    duplicate_candidates = set()
    invalid_references = set()

    rows_preview = []
    valid_count = 0
    invalid_count = 0
    warning_count = 0

    for i, row in enumerate(rows, start=2):
        row_errors = []
        row_warnings = []

        fn = row.get("first_name", "").strip()
        ln = row.get("last_name", "").strip()
        adm = row.get("admission_number", "").strip()
        gen = row.get("gender", "").strip().upper()
        c_name = row.get("class_name", "").strip()
        s_name = row.get("section_name", "").strip()

        if not fn:
            row_errors.append("Required field 'first_name' is empty")
        if not ln:
            row_errors.append("Required field 'last_name' is empty")
        if not adm:
            row_errors.append("Required field 'admission_number' is empty")
        if not gen:
            row_errors.append("Required field 'gender' is empty")
        elif gen not in valid_genders:
            row_errors.append(f"Invalid gender '{gen}'. Valid: {sorted(valid_genders)}")

        # Check DB duplicate
        if adm:
            if adm.lower() in seen_admissions:
                row_errors.append(f"Duplicate admission number '{adm}' in file batch")
                duplicate_candidates.add(adm)
            else:
                seen_admissions.add(adm.lower())
                dup_db = db.execute(
                    select(Student).where(
                        Student.school_id == school_id,
                        func.lower(Student.admission_number) == adm.lower(),
                        Student.is_deleted.is_(False),
                    )
                ).scalar_one_or_none()
                if dup_db:
                    row_errors.append(f"Admission number '{adm}' already exists in database")
                    duplicate_candidates.add(adm)

        # Check academic year
        ay_name = row.get("academic_year_name", "").strip()
        academic_year = _get_academic_year_by_name(db, school_id, ay_name) if ay_name else _get_current_academic_year(db, school_id)
        if not academic_year:
            row_errors.append("No active academic year found in school")
            invalid_references.add("Academic Year")

        if not row.get("roll_number", "").strip():
            row_warnings.append("roll_number is empty (will default to admission_number)")
        if not row.get("parent_phone", "").strip():
            row_warnings.append("parent_phone is empty (will generate default parent profile)")

        if row_errors:
            status_val = "BLOCKING_ERROR"
            invalid_count += 1
        elif row_warnings:
            status_val = "WARNING"
            warning_count += 1
            valid_count += 1
        else:
            status_val = "VALID"
            valid_count += 1

        rows_preview.append(
            {
                "row_number": i,
                "status": status_val,
                "admission_number": adm,
                "first_name": fn,
                "last_name": ln,
                "class_name": c_name,
                "section_name": s_name,
                "errors": row_errors,
                "warnings": row_warnings,
            }
        )

    return {
        "total_rows": len(rows),
        "valid_rows_count": valid_count,
        "invalid_rows_count": invalid_count,
        "warning_rows_count": warning_count,
        "duplicate_candidates": sorted(list(duplicate_candidates)),
        "invalid_references": sorted(list(invalid_references)),
        "can_commit": (invalid_count == 0),
        "rows_preview": rows_preview,
    }


def commit_student_import(
    db: Session,
    file_content: bytes,
    filename: str,
    school_id: UUID,
    atomic_mode: bool = True,
) -> dict:
    preview = preview_student_import(db, file_content, filename, school_id)

    if atomic_mode and not preview["can_commit"]:
        return {
            "success": False,
            "committed_rows": 0,
            "skipped_rows": preview["total_rows"],
            "failed_rows": preview["invalid_rows_count"],
            "message": f"Atomic commit failed: {preview['invalid_rows_count']} rows have blocking validation errors. 0 students created.",
            "errors": [
                {"row_number": r["row_number"], "errors": r["errors"]}
                for r in preview["rows_preview"] if r["status"] == "BLOCKING_ERROR"
            ],
        }

    # Perform atomic or partial import
    result = ImportResult(entity_type="students")
    fname_lower = filename.lower()
    if fname_lower.endswith((".xlsx", ".xls")):
        rows = parse_xlsx_bytes(file_content)
    else:
        rows = parse_csv_bytes(file_content)

    savepoint = db.begin_nested()
    try:
        _import_students(db, rows or [], school_id, result)
        if atomic_mode and result.invalid_rows > 0:
            savepoint.rollback()
            return {
                "success": False,
                "committed_rows": 0,
                "skipped_rows": result.total_rows,
                "failed_rows": result.invalid_rows,
                "message": "Atomic import failed during database stage. All student creations rolled back.",
                "errors": [{"row_number": e.row_number, "message": e.message} for e in result.errors],
            }
        db.commit()
    except Exception as exc:
        savepoint.rollback()
        logger.exception("Atomic student import exception: %s", exc)
        return {
            "success": False,
            "committed_rows": 0,
            "skipped_rows": result.total_rows,
            "failed_rows": result.total_rows,
            "message": f"Fatal database error during import. All changes rolled back: {exc}",
            "errors": [{"row_number": 0, "message": str(exc)}],
        }

    return {
        "success": True,
        "committed_rows": result.inserted_rows,
        "skipped_rows": result.skipped_rows,
        "failed_rows": result.invalid_rows,
        "message": f"Successfully onboarded {result.inserted_rows} student records.",
        "errors": [{"row_number": e.row_number, "message": e.message} for e in result.errors],
    }

