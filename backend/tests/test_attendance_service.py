import uuid
from datetime import date
import pytest

from app.common.enums import AttendanceStatus, Gender, StudentStatus
from app.common.enums.parent import ParentRelationship
from app.common.exceptions.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.identity.models import IdentityUser
from app.models.academic_year.academic_year import AcademicYear
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.schemas.academic_year import AcademicYearCreate
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceBulkItem,
    AttendanceCreate,
    AttendanceUpdate,
)
from app.services.academic_year_service import academic_year_service
from app.services.attendance_service import attendance_service


def setup_attendance_fixtures(db, school_name="Att Service School", code_prefix="ATS"):
    """
    Helper function to set up School, AcademicYear, SchoolClass, Section, Parent,
    and active Students for attendance testing.
    """
    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{code_prefix[:4]}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Education Way",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()

    ay_in = AcademicYearCreate(
        school_id=school.id,
        name=f"2026-2027-{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    academic_year = academic_year_service.create_academic_year(db, ay_in)

    sclass = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 10",
        display_order=10,
    )
    db.add(sclass)

    section = Section(
        id=uuid.uuid4(),
        school_class_id=sclass.id,
        name="Section A",
    )
    db.add(section)

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Suresh Sharma",
        primary_phone=f"9{uuid.uuid4().int % 1000000009:09d}",
        relationship=ParentRelationship.FATHER,
        address_line1="5 Park Lane",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()

    student1 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=academic_year.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="101",
        first_name="Aarav",
        last_name="Sharma",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2026, 4, 1),
        address_line1="5 Park Lane",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    student2 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=academic_year.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="102",
        first_name="Vivaan",
        last_name="Sharma",
        gender=Gender.MALE,
        date_of_birth=date(2010, 2, 1),
        admission_date=date(2026, 4, 1),
        address_line1="5 Park Lane",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    db.add_all([student1, student2])
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"teacher_{uuid.uuid4().hex[:6]}@school.com",
        password_hash="hashed_pass",
        first_name="Teacher",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    return school, academic_year, sclass, section, student1, student2, user


def test_attendance_status_enum_values():
    assert AttendanceStatus.PRESENT.value == "PRESENT"
    assert AttendanceStatus.ABSENT.value == "ABSENT"
    assert AttendanceStatus.LATE.value == "LATE"
    assert AttendanceStatus.HALF_DAY.value == "HALF_DAY"
    assert AttendanceStatus.EXCUSED.value == "EXCUSED"


def test_create_and_get_attendance(db_session):
    school, ay, sclass, section, s1, s2, user = setup_attendance_fixtures(db_session)

    att_in = AttendanceCreate(
        student_id=s1.id,
        attendance_date=date(2026, 8, 1),
        status=AttendanceStatus.PRESENT,
        remarks="On time",
    )
    created = attendance_service.create_attendance(db_session, user, att_in)
    assert created.id is not None
    assert created.student_id == s1.id
    assert created.school_id == school.id
    assert created.status == AttendanceStatus.PRESENT

    retrieved = attendance_service.get_attendance(db_session, user, created.id)
    assert retrieved.id == created.id
    assert retrieved.remarks == "On time"


def test_duplicate_attendance_rejected(db_session):
    school, ay, sclass, section, s1, s2, user = setup_attendance_fixtures(db_session, "Dup School")

    att_in = AttendanceCreate(
        student_id=s1.id,
        attendance_date=date(2026, 8, 2),
        status=AttendanceStatus.PRESENT,
    )
    attendance_service.create_attendance(db_session, user, att_in)

    with pytest.raises(AlreadyExistsException):
        attendance_service.create_attendance(db_session, user, att_in)


def test_bulk_create_attendance_success(db_session):
    school, ay, sclass, section, s1, s2, user = setup_attendance_fixtures(db_session, "Bulk School")

    bulk_in = AttendanceBulkCreate(
        section_id=section.id,
        attendance_date=date(2026, 8, 3),
        records=[
            AttendanceBulkItem(student_id=s1.id, status=AttendanceStatus.PRESENT),
            AttendanceBulkItem(student_id=s2.id, status=AttendanceStatus.ABSENT, remarks="Sick"),
        ],
    )
    result = attendance_service.create_bulk_attendance(db_session, user, bulk_in)
    assert len(result) == 2
    assert result[0].status == AttendanceStatus.PRESENT
    assert result[1].status == AttendanceStatus.ABSENT


def test_bulk_create_atomicity_on_existing_record(db_session):
    school, ay, sclass, section, s1, s2, user = setup_attendance_fixtures(db_session, "Atomic School")

    # Mark attendance for s1 first
    att_in = AttendanceCreate(
        student_id=s1.id,
        attendance_date=date(2026, 8, 4),
        status=AttendanceStatus.PRESENT,
    )
    attendance_service.create_attendance(db_session, user, att_in)

    # Bulk create for s1 and s2 on same date should fail atomically
    bulk_in = AttendanceBulkCreate(
        section_id=section.id,
        attendance_date=date(2026, 8, 4),
        records=[
            AttendanceBulkItem(student_id=s1.id, status=AttendanceStatus.PRESENT),
            AttendanceBulkItem(student_id=s2.id, status=AttendanceStatus.PRESENT),
        ],
    )
    with pytest.raises(AlreadyExistsException):
        attendance_service.create_bulk_attendance(db_session, user, bulk_in)

    # Verify s2 attendance was NOT created (no partial write)
    items, total, _ = attendance_service.list_attendance(
        db_session, user, student_id=s2.id, attendance_date=date(2026, 8, 4)
    )
    assert total == 0


def test_update_and_soft_delete_attendance(db_session):
    school, ay, sclass, section, s1, s2, user = setup_attendance_fixtures(db_session, "Update School")

    created = attendance_service.create_attendance(
        db_session,
        user,
        AttendanceCreate(
            student_id=s1.id,
            attendance_date=date(2026, 8, 5),
            status=AttendanceStatus.ABSENT,
        ),
    )
    assert created.status == AttendanceStatus.ABSENT

    updated = attendance_service.update_attendance(
        db_session,
        user,
        created.id,
        AttendanceUpdate(status=AttendanceStatus.EXCUSED, remarks="Medical Certificate"),
    )
    assert updated.status == AttendanceStatus.EXCUSED
    assert updated.remarks == "Medical Certificate"

    attendance_service.delete_attendance(db_session, user, created.id)

    with pytest.raises(NotFoundException):
        attendance_service.get_attendance(db_session, user, created.id)


def test_student_section_mismatch_rejected(db_session):
    school, ay, sclass, section, s1, s2, user = setup_attendance_fixtures(db_session, "Mismatch School")

    sec2 = Section(
        id=uuid.uuid4(),
        school_class_id=sclass.id,
        name="Section B",
    )
    db_session.add(sec2)
    db_session.commit()

    bulk_in = AttendanceBulkCreate(
        section_id=sec2.id,
        attendance_date=date(2026, 8, 6),
        records=[
            AttendanceBulkItem(student_id=s1.id, status=AttendanceStatus.PRESENT),
        ],
    )
    with pytest.raises(ValidationException):
        attendance_service.create_bulk_attendance(db_session, user, bulk_in)


def test_student_another_school_rejected(db_session):
    school1, ay1, sclass1, sec1, s1, s2, user1 = setup_attendance_fixtures(db_session, "School 1")
    school2, ay2, sclass2, sec2, s3, s4, user2 = setup_attendance_fixtures(db_session, "School 2")

    # Attempt user2 creating attendance for s1 (from School 1)
    att_in = AttendanceCreate(
        student_id=s1.id,
        attendance_date=date(2026, 8, 7),
        status=AttendanceStatus.PRESENT,
    )
    with pytest.raises(NotFoundException):
        attendance_service.create_attendance(db_session, user2, att_in)


def test_recreate_attendance_after_soft_delete(db_session):
    """
    Verify:
    1. Active attendance record prevents duplicate creation on same student & date.
    2. After soft deletion, a new attendance record for the same student & date can be created.
    """
    school, ay, sclass, section, s1, s2, user = setup_attendance_fixtures(
        db_session, "Recreate School"
    )
    att_date = date(2026, 8, 10)

    # 1. Create initial attendance record
    att1 = attendance_service.create_attendance(
        db_session,
        user,
        AttendanceCreate(
            student_id=s1.id,
            attendance_date=att_date,
            status=AttendanceStatus.PRESENT,
        ),
    )
    assert att1.id is not None
    assert att1.is_deleted is False

    # 2. Attempt duplicate creation when active -> raises AlreadyExistsException
    with pytest.raises(AlreadyExistsException):
        attendance_service.create_attendance(
            db_session,
            user,
            AttendanceCreate(
                student_id=s1.id,
                attendance_date=att_date,
                status=AttendanceStatus.ABSENT,
            ),
        )

    # 3. Soft delete initial attendance record
    attendance_service.delete_attendance(db_session, user, att1.id)
    assert att1.is_deleted is True

    # 4. Re-create attendance for same student & date after soft delete -> succeeds
    att2 = attendance_service.create_attendance(
        db_session,
        user,
        AttendanceCreate(
            student_id=s1.id,
            attendance_date=att_date,
            status=AttendanceStatus.LATE,
            remarks="Re-created after soft delete",
        ),
    )
    assert att2.id != att1.id
    assert att2.status == AttendanceStatus.LATE
    assert att2.is_deleted is False
