"""
Phase 30.9 — Legacy Data Migration & Bulk Onboarding Subsystem Tests (GAP-05)
Comprehensive verification for:
1. Legacy Fee Structures import
2. Outstanding Fee Balances migration (Opening Balances without fake payment receipts)
3. Historical Marks & Examination Results import (Idempotent & bounded)
4. Dry-Run Savepoint Isolation (Zero persistent database mutations during preview)
5. Atomic vs Non-Atomic Commit Rollback Guarantees
6. RBAC & Multi-Tenant Isolation
"""
import io
import csv
import uuid
from decimal import Decimal
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.identity.models import (
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import permission_repository
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student, Gender
from app.models.subject.subject import Subject
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.parent.parent import Parent
from app.common.enums.fees import StudentFeeAssignmentStatus
from app.models.fees.fee_structure import FeeStructure, FeeItem, FeeCategory
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.fees.fee_payment import FeePayment
from app.services.import_service import (
    preview_import,
    commit_import,
    import_data,
)


def create_school_and_user(db: Session, perms: list[str]) -> tuple[School, dict[str, str], IdentityUser]:
    """Helper to create school, role with specific permissions, user, and authorization headers."""
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=f"Migration School {uuid.uuid4().hex[:4]}",
        code=f"MIG{uuid.uuid4().hex[:4].upper()}",
        address_line1="1 Migration Way",
        city="Bengaluru",
        district="Bengaluru Urban",
        state="Karnataka",
        country="India",
        postal_code="560001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Migration Test Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in perms:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"migrator_{uuid.uuid4().hex[:6]}@school.edu",
        password_hash=hash_password("SecurePass123!"),
        first_name="Data",
        last_name="Admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, headers, user


def make_csv_bytes(rows: list[dict], fieldnames: list[str]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


# ══════════════════════════════════════════════════════════════════
# 1. Legacy Fee Structures Tests
# ══════════════════════════════════════════════════════════════════

class TestLegacyFeeStructuresMigration:

    def _setup_fixtures(self, db: Session, school: School):
        ay = AcademicYear(
            id=uuid.uuid4(),
            school_id=school.id,
            name="2024-2025",
            start_date=date(2024, 6, 1),
            end_date=date(2025, 4, 30),
            is_current=True,
        )
        sc = SchoolClass(
            id=uuid.uuid4(),
            school_id=school.id,
            name="Grade 10",
            display_order=10,
        )
        db.add_all([ay, sc])
        db.commit()
        return ay, sc

    def test_fee_structure_import_success(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["fees.create"])
        ay, sc = self._setup_fixtures(db_session, school)

        fieldnames = ["academic_year", "fee_structure_name", "item_name", "item_category", "amount", "class_name", "is_optional", "description"]
        rows = [
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Grade 10 Annual Fee",
                "item_name": "Tuition Term 1",
                "item_category": "TUITION",
                "amount": "25000.50",
                "class_name": "Grade 10",
                "is_optional": "false",
                "description": "Term 1 tuition",
            },
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Grade 10 Annual Fee",
                "item_name": "Examination Fee",
                "item_category": "EXAMINATION",
                "amount": "4500.00",
                "class_name": "Grade 10",
                "is_optional": "false",
                "description": "Board exam fee",
            },
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/fee_structures/commit",
            files={"file": ("fee_structures.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["inserted_rows"] == 2

        # Verify DB records
        struct = db_session.query(FeeStructure).filter_by(school_id=school.id, name="Grade 10 Annual Fee").first()
        assert struct is not None
        assert struct.academic_year_id == ay.id
        assert struct.school_class_id == sc.id
        assert len(struct.items) == 2
        
        item_names = {i.name: i.amount for i in struct.items}
        assert item_names["Tuition Term 1"] == Decimal("25000.50")
        assert item_names["Examination Fee"] == Decimal("4500.00")

    def test_fee_structure_import_invalid_category_rejected(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["fees.create"])
        self._setup_fixtures(db_session, school)

        fieldnames = ["academic_year", "fee_structure_name", "item_name", "item_category", "amount", "class_name"]
        rows = [
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Grade 10 Fee",
                "item_name": "Random Fee",
                "item_category": "NON_EXISTENT_CATEGORY",
                "amount": "1000.00",
                "class_name": "Grade 10",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/fee_structures/preview",
            files={"file": ("fee_structures.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["invalid_rows"] == 1
        assert data["can_commit"] is False
        assert "Invalid fee category" in data["errors"][0]["message"]

    def test_fee_structure_import_non_numeric_amount_rejected(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["fees.create"])
        self._setup_fixtures(db_session, school)

        fieldnames = ["academic_year", "fee_structure_name", "item_name", "item_category", "amount", "class_name"]
        rows = [
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Grade 10 Fee",
                "item_name": "Tuition Fee",
                "item_category": "TUITION",
                "amount": "INVALID_AMOUNT",
                "class_name": "Grade 10",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/fee_structures/preview",
            files={"file": ("fee_structures.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["invalid_rows"] == 1
        assert "Invalid monetary amount" in data["errors"][0]["message"]


# ══════════════════════════════════════════════════════════════════
# 2. Outstanding Fee Balances Tests (Opening Balances)
# ══════════════════════════════════════════════════════════════════

class TestOutstandingBalancesMigration:

    def _setup_student(self, db: Session, school: School, adm_no: str = "ADM-LEGACY-001") -> tuple[AcademicYear, Student]:
        ay = AcademicYear(
            id=uuid.uuid4(),
            school_id=school.id,
            name="2023-2024",
            start_date=date(2023, 6, 1),
            end_date=date(2024, 4, 30),
            is_current=False,
        )
        sc = SchoolClass(
            id=uuid.uuid4(),
            school_id=school.id,
            name="Grade 8",
            display_order=8,
        )
        db.add_all([ay, sc])
        db.flush()

        sec = Section(
            id=uuid.uuid4(),
            school_class_id=sc.id,
            name="A",
        )
        parent = Parent(
            id=uuid.uuid4(),
            school_id=school.id,
            father_name="Rohan Father",
            guardian_name="Rohan Father",
            relationship="FATHER",
            primary_phone=f"987{uuid.uuid4().hex[:7]}",
            address_line1="N/A",
            city="Bengaluru",
            district="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560001",
        )
        db.add_all([sec, parent])
        db.flush()

        student = Student(
            id=uuid.uuid4(),
            school_id=school.id,
            academic_year_id=ay.id,
            school_class_id=sc.id,
            section_id=sec.id,
            parent_id=parent.id,
            first_name="Rohan",
            last_name="Verma",
            admission_number=adm_no,
            roll_number=adm_no,
            gender=Gender.MALE,
            date_of_birth=date(2008, 3, 15),
            admission_date=date(2023, 6, 1),
            address_line1="123 Test Street",
            city="Bengaluru",
            district="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560001",
        )
        db.add(student)
        db.commit()
        return ay, student

    def test_outstanding_balance_import_success_no_fake_payments(self, client, db_session):
        """Opening balance must create assignment and item but ZERO FeePayment records."""
        school, headers, _ = create_school_and_user(db_session, ["fees.create"])
        ay, student = self._setup_student(db_session, school, "ADM-LEGACY-001")

        fieldnames = ["admission_number", "academic_year", "fee_name", "assessed_amount", "paid_amount", "due_date", "remarks"]
        rows = [
            {
                "admission_number": "ADM-LEGACY-001",
                "academic_year": "2023-2024",
                "fee_name": "Legacy Tuition Arrears",
                "assessed_amount": "20000.00",
                "paid_amount": "8000.00",
                "due_date": "2024-03-31",
                "remarks": "Carried forward from old system",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/outstanding_balances/commit",
            files={"file": ("balances.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["success"] is True
        assert data["inserted_rows"] == 1

        # Check DB State
        assignment = db_session.query(StudentFeeAssignment).filter_by(
            school_id=school.id,
            student_id=student.id,
        ).first()
        assert assignment is not None
        assert assignment.status == StudentFeeAssignmentStatus.PARTIALLY_PAID

        fee_items = db_session.query(StudentFeeItem).filter_by(
            student_fee_assignment_id=assignment.id,
        ).all()
        assert len(fee_items) == 1
        assert fee_items[0].name == "Legacy Tuition Arrears"
        assert fee_items[0].amount == Decimal("20000.00")
        assert fee_items[0].category == FeeCategory.MISCELLANEOUS

        # Verify absolutely NO fake FeePayment rows were created
        payments = db_session.query(FeePayment).filter_by(school_id=school.id).all()
        assert len(payments) == 0

    def test_outstanding_balance_paid_greater_than_assessed_rejected(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["fees.create"])
        self._setup_student(db_session, school, "ADM-LEGACY-002")

        fieldnames = ["admission_number", "academic_year", "fee_name", "assessed_amount", "paid_amount"]
        rows = [
            {
                "admission_number": "ADM-LEGACY-002",
                "academic_year": "2023-2024",
                "fee_name": "Tuition Arrears",
                "assessed_amount": "10000.00",
                "paid_amount": "15000.00",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/outstanding_balances/preview",
            files={"file": ("balances.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["invalid_rows"] == 1
        assert "must be between 0 and assessed amount" in data["errors"][0]["message"]

    def test_outstanding_balance_unknown_student_rejected(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["fees.create"])
        self._setup_student(db_session, school, "ADM-LEGACY-003")

        fieldnames = ["admission_number", "academic_year", "fee_name", "assessed_amount", "paid_amount"]
        rows = [
            {
                "admission_number": "NON_EXISTENT_STUDENT",
                "academic_year": "2023-2024",
                "fee_name": "Tuition Arrears",
                "assessed_amount": "10000.00",
                "paid_amount": "0.00",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/outstanding_balances/preview",
            files={"file": ("balances.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["reference_errors"] == 1
        assert "not found" in data["errors"][0]["message"]


# ══════════════════════════════════════════════════════════════════
# 3. Historical Marks Tests
# ══════════════════════════════════════════════════════════════════

class TestHistoricalMarksMigration:

    def _setup_fixtures(self, db: Session, school: School, adm_no: str = "ADM-HIST-001"):
        ay = AcademicYear(
            id=uuid.uuid4(),
            school_id=school.id,
            name="2023-2024",
            start_date=date(2023, 6, 1),
            end_date=date(2024, 4, 30),
            is_current=False,
        )
        sc = SchoolClass(
            id=uuid.uuid4(),
            school_id=school.id,
            name="Grade 9",
            display_order=9,
        )
        db.add_all([ay, sc])
        db.flush()

        sec = Section(
            id=uuid.uuid4(),
            school_class_id=sc.id,
            name="A",
        )
        sub = Subject(
            id=uuid.uuid4(),
            school_id=school.id,
            subject_name="Mathematics",
            subject_code="MATH-101",
        )
        parent = Parent(
            id=uuid.uuid4(),
            school_id=school.id,
            father_name="Ananya Father",
            guardian_name="Ananya Father",
            relationship="FATHER",
            primary_phone=f"986{uuid.uuid4().hex[:7]}",
            address_line1="N/A",
            city="Bengaluru",
            district="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560001",
        )
        db.add_all([sec, sub, parent])
        db.flush()

        student = Student(
            id=uuid.uuid4(),
            school_id=school.id,
            academic_year_id=ay.id,
            school_class_id=sc.id,
            section_id=sec.id,
            parent_id=parent.id,
            first_name="Ananya",
            last_name="Deshmukh",
            admission_number=adm_no,
            roll_number=adm_no,
            gender=Gender.FEMALE,
            date_of_birth=date(2009, 8, 20),
            admission_date=date(2023, 6, 1),
            address_line1="456 Academic Road",
            city="Bengaluru",
            district="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560001",
        )
        db.add(student)
        db.commit()
        return ay, sc, sec, sub, student

    def test_historical_marks_import_success_and_idempotence(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["marks.create"])
        ay, sc, sec, sub, student = self._setup_fixtures(db_session, school, "ADM-HIST-001")

        fieldnames = [
            "admission_number", "academic_year", "class_name", "section_name",
            "exam_name", "subject_code", "marks_obtained", "max_marks", "passing_marks", "remarks"
        ]
        rows = [
            {
                "admission_number": "ADM-HIST-001",
                "academic_year": "2023-2024",
                "class_name": "Grade 9",
                "section_name": "A",
                "exam_name": "Final Term 2024",
                "subject_code": "MATH-101",
                "marks_obtained": "92.50",
                "max_marks": "100.00",
                "passing_marks": "35.00",
                "remarks": "Excellent performance",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        # 1. First import
        response = client.post(
            "/api/v1/import/historical_marks/commit",
            files={"file": ("marks.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["inserted_rows"] == 1

        result = db_session.query(StudentExamResult).filter_by(
            student_id=student.id,
        ).first()
        assert result is not None
        assert result.marks_obtained == Decimal("92.50")
        assert result.remarks == "Excellent performance"

        # 2. Idempotent re-import with updated mark
        rows[0]["marks_obtained"] = "95.00"
        rows[0]["remarks"] = "Updated recheck score"
        content_updated = make_csv_bytes(rows, fieldnames)

        response2 = client.post(
            "/api/v1/import/historical_marks/commit",
            files={"file": ("marks.csv", content_updated, "text/csv")},
            headers=headers,
        )
        assert response2.status_code == 200
        assert response2.json()["updated_rows"] == 1
        assert response2.json()["inserted_rows"] == 0

        db_session.refresh(result)
        assert result.marks_obtained == Decimal("95.00")
        assert result.remarks == "Updated recheck score"

    def test_historical_marks_exceeds_max_rejected(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["marks.create"])
        self._setup_fixtures(db_session, school, "ADM-HIST-002")

        fieldnames = [
            "admission_number", "academic_year", "class_name", "section_name",
            "exam_name", "subject_code", "marks_obtained", "max_marks"
        ]
        rows = [
            {
                "admission_number": "ADM-HIST-002",
                "academic_year": "2023-2024",
                "class_name": "Grade 9",
                "section_name": "A",
                "exam_name": "Mid Term 2024",
                "subject_code": "MATH-101",
                "marks_obtained": "105.00",
                "max_marks": "100.00",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/historical_marks/preview",
            files={"file": ("marks.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["invalid_rows"] == 1
        assert "exceeds max marks" in data["errors"][0]["message"]


# ══════════════════════════════════════════════════════════════════
# 4. Dry-Run Savepoint Isolation Tests
# ══════════════════════════════════════════════════════════════════

class TestDryRunSavepointIsolation:

    def test_preview_makes_zero_persistent_database_mutations(self, client, db_session):
        """Previewing import must rollback completely and leave 0 DB artifacts."""
        school, headers, _ = create_school_and_user(db_session, ["fees.create", "marks.create"])
        
        ay = AcademicYear(
            id=uuid.uuid4(),
            school_id=school.id,
            name="2024-2025",
            start_date=date(2024, 6, 1),
            end_date=date(2025, 4, 30),
            is_current=True,
        )
        sc = SchoolClass(
            id=uuid.uuid4(),
            school_id=school.id,
            name="Grade 8",
            display_order=8,
        )
        db_session.add_all([ay, sc])
        db_session.commit()

        initial_structures = db_session.query(FeeStructure).filter_by(school_id=school.id).count()
        assert initial_structures == 0

        fieldnames = ["academic_year", "fee_structure_name", "item_name", "item_category", "amount", "class_name"]
        rows = [
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Dry Run Test Structure",
                "item_name": "Tuition Fee",
                "item_category": "TUITION",
                "amount": "12000.00",
                "class_name": "Grade 8",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/fee_structures/preview",
            files={"file": ("structures.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["can_commit"] is True

        # Ensure DB has 0 persistent fee structures
        db_structures_after = db_session.query(FeeStructure).filter_by(school_id=school.id).count()
        assert db_structures_after == 0


# ══════════════════════════════════════════════════════════════════
# 5. Atomic Rollback Guarantees
# ══════════════════════════════════════════════════════════════════

class TestAtomicRollbackGuarantees:

    def test_atomic_mode_rolls_back_on_any_row_failure(self, client, db_session):
        school, headers, _ = create_school_and_user(db_session, ["fees.create"])
        
        ay = AcademicYear(
            id=uuid.uuid4(),
            school_id=school.id,
            name="2024-2025",
            start_date=date(2024, 6, 1),
            end_date=date(2025, 4, 30),
            is_current=True,
        )
        sc = SchoolClass(
            id=uuid.uuid4(),
            school_id=school.id,
            name="Grade 7",
            display_order=7,
        )
        db_session.add_all([ay, sc])
        db_session.commit()

        fieldnames = ["academic_year", "fee_structure_name", "item_name", "item_category", "amount", "class_name"]
        rows = [
            # Row 1: Valid
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Grade 7 Fee",
                "item_name": "Tuition",
                "item_category": "TUITION",
                "amount": "10000.00",
                "class_name": "Grade 7",
            },
            # Row 2: Invalid (Unknown category)
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Grade 7 Fee",
                "item_name": "Invalid Item",
                "item_category": "BAD_CATEGORY_NAME",
                "amount": "2000.00",
                "class_name": "Grade 7",
            },
        ]
        content = make_csv_bytes(rows, fieldnames)

        # Atomic commit should fail with 422 and insert 0 rows
        response = client.post(
            "/api/v1/import/fee_structures/commit?atomic_mode=true",
            files={"file": ("structures.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["inserted_rows"] == 0

        # Verify DB has 0 records
        assert db_session.query(FeeStructure).filter_by(school_id=school.id).count() == 0


# ══════════════════════════════════════════════════════════════════
# 6. RBAC & Multi-Tenant Isolation
# ══════════════════════════════════════════════════════════════════

class TestRBACAndTenantIsolation:

    def test_user_without_permission_receives_403(self, client, db_session):
        # User only has student.view, not fees.create
        _, headers, _ = create_school_and_user(db_session, ["student.view"])

        content = b"academic_year,fee_structure_name,item_name,item_category,amount,class_name\n"
        response = client.post(
            "/api/v1/import/fee_structures/preview",
            files={"file": ("fee.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 403

    def test_tenant_isolation_prevents_cross_school_mutation(self, client, db_session):
        school_a, headers_a, _ = create_school_and_user(db_session, ["fees.create"])
        school_b, headers_b, _ = create_school_and_user(db_session, ["fees.create"])

        ay_b = AcademicYear(
            id=uuid.uuid4(),
            school_id=school_b.id,
            name="2024-2025",
            start_date=date(2024, 6, 1),
            end_date=date(2025, 4, 30),
            is_current=True,
        )
        sc_b = SchoolClass(
            id=uuid.uuid4(),
            school_id=school_b.id,
            name="Grade 11",
            display_order=11,
        )
        db_session.add_all([ay_b, sc_b])
        db_session.commit()

        # School A tries to import for Academic Year that only exists in School B
        fieldnames = ["academic_year", "fee_structure_name", "item_name", "item_category", "amount", "class_name"]
        rows = [
            {
                "academic_year": "2024-2025",
                "fee_structure_name": "Grade 11 Fee",
                "item_name": "Tuition",
                "item_category": "TUITION",
                "amount": "15000.00",
                "class_name": "Grade 11",
            }
        ]
        content = make_csv_bytes(rows, fieldnames)

        response = client.post(
            "/api/v1/import/fee_structures/preview",
            files={"file": ("fee.csv", content, "text/csv")},
            headers=headers_a,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # School A should get reference error because 2024-2025 doesn't exist for School A
        assert data["reference_errors"] >= 1
