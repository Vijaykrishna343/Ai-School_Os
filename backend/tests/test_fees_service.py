import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.common.enums import Gender, StudentStatus
from app.common.enums.fees import (
    DiscountType,
    FeeCategory,
    FeeStructureStatus,
    PaymentMode,
    StudentFeeAssignmentStatus,
)
from app.common.enums.parent import ParentRelationship
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.models.academic_year.academic_year import AcademicYear
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.schemas.fees.fees import (
    FeeDiscountCreate,
    FeeItemCreate,
    FeePaymentCreate,
    FeeStructureCreate,
    FeeStructureUpdate,
    StudentFeeAssignmentCreate,
    StudentFeeItemCreate,
)
from app.services.fee_service import fee_service


def create_test_school(db, name="Fees School", code="FSCH"):
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="10 Fee St",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def create_test_academic_year(db, school_id, name="2026-2027"):
    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_id,
        name=f"{name}_{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay


def create_test_class_and_section(db, school_id, name="Class 5"):
    sc = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_id,
        name=f"{name}_{uuid.uuid4().hex[:4]}",
        display_order=1,
    )
    db.add(sc)
    db.commit()

    sec = Section(
        id=uuid.uuid4(),
        school_class_id=sc.id,
        name="Section A",
    )
    db.add(sec)
    db.commit()
    db.refresh(sc)
    db.refresh(sec)
    return sc, sec


def create_test_parent(db, school_id):
    parent = Parent(
        id=uuid.uuid4(),
        school_id=school_id,
        father_name="Parent User",
        primary_phone=f"9{uuid.uuid4().int % 1000000009:09d}",
        relationship=ParentRelationship.FATHER,
        address_line1="100 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def create_test_student(
    db,
    school_id,
    academic_year_id=None,
    school_class_id=None,
    section_id=None,
    parent_id=None,
    status=StudentStatus.ACTIVE,
):
    if academic_year_id is None:
        academic_year_id = create_test_academic_year(db, school_id).id
    if school_class_id is None or section_id is None:
        sc, sec = create_test_class_and_section(db, school_id)
        school_class_id = sc.id
        section_id = sec.id
    if parent_id is None:
        parent_id = create_test_parent(db, school_id).id

    student = Student(
        id=uuid.uuid4(),
        school_id=school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        parent_id=parent_id,
        admission_number=f"ADM_{uuid.uuid4().hex[:6]}",
        roll_number=f"R_{uuid.uuid4().hex[:4]}",
        first_name="John",
        last_name="Doe",
        gender=Gender.MALE,
        date_of_birth=date(2012, 1, 1),
        admission_date=date(2026, 4, 1),
        address_line1="100 Student St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=status,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def test_fee_structure_create_and_validations(db_session):
    db = db_session
    school = create_test_school(db, "Fee School 1", "FS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    sc, _ = create_test_class_and_section(db, school.id, "Class 1")

    items = [
        FeeItemCreate(
            category=FeeCategory.TUITION,
            name="Tuition Fee",
            amount=Decimal("20000.00"),
            is_optional=False,
            order=1,
        ),
        FeeItemCreate(
            category=FeeCategory.TRANSPORTATION,
            name="Bus Fee",
            amount=Decimal("8000.00"),
            is_optional=True,
            order=2,
        ),
    ]

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        school_class_id=sc.id,
        name="Class 1 Fee Structure",
        description="Standard Class 1 fees",
        status=FeeStructureStatus.ACTIVE,
        items=items,
    )

    created = fee_service.create_fee_structure(db, struct_data, school.id)
    assert created.id is not None
    assert created.name == "Class 1 Fee Structure"
    assert len(created.items) == 2

    # Duplicate active name rejection
    with pytest.raises(AlreadyExistsException):
        fee_service.create_fee_structure(db, struct_data, school.id)


def test_fee_structure_cross_school_academic_year_rejected(db_session):
    db = db_session
    school1 = create_test_school(db, "Fee School A", "FSA")
    school2 = create_test_school(db, "Fee School B", "FSB")

    ay2 = create_test_academic_year(db, school2.id, "2026-27")

    struct_data = FeeStructureCreate(
        academic_year_id=ay2.id,
        name="Cross School Structure",
        items=[],
    )

    with pytest.raises(ValidationException):
        fee_service.create_fee_structure(db, struct_data, school1.id)


def test_fee_structure_update_and_soft_delete(db_session):
    db = db_session
    school = create_test_school(db, "Update School", "US1")
    ay = create_test_academic_year(db, school.id, "2026-27")

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        name="Original Name",
        status=FeeStructureStatus.DRAFT,
        items=[
            FeeItemCreate(
                category=FeeCategory.TUITION,
                name="Tuition Fee",
                amount=Decimal("10000.00"),
            )
        ],
    )
    structure = fee_service.create_fee_structure(db, struct_data, school.id)

    update_data = FeeStructureUpdate(
        name="Updated Name",
        status=FeeStructureStatus.ACTIVE,
    )
    updated = fee_service.update_fee_structure(db, structure.id, update_data, school.id)
    assert updated.name == "Updated Name"
    assert updated.status == FeeStructureStatus.ACTIVE

    fee_service.delete_fee_structure(db, structure.id, school.id)
    with pytest.raises(NotFoundException):
        fee_service.get_fee_structure(db, structure.id, school.id)


def test_student_fee_assignment_and_validations(db_session):
    db = db_session
    school = create_test_school(db, "Assign School", "AS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    sc, sec = create_test_class_and_section(db, school.id, "Class 5")
    parent = create_test_parent(db, school.id)
    student = create_test_student(
        db, school.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=parent.id
    )

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        school_class_id=sc.id,
        name="Class 5 Fee Structure",
        status=FeeStructureStatus.ACTIVE,
        items=[
            FeeItemCreate(
                category=FeeCategory.TUITION,
                name="Tuition Fee",
                amount=Decimal("20000.00"),
            ),
            FeeItemCreate(
                category=FeeCategory.EXAMINATION,
                name="Exam Fee",
                amount=Decimal("2000.00"),
            ),
        ],
    )
    structure = fee_service.create_fee_structure(db, struct_data, school.id)

    assign_data = StudentFeeAssignmentCreate(
        academic_year_id=ay.id,
        student_id=student.id,
        fee_structure_id=structure.id,
        due_date=date(2026, 6, 30),
    )

    assignment = fee_service.assign_fee_structure(db, assign_data, school.id)
    assert assignment.id is not None
    assert assignment.gross_amount == Decimal("22000.00")
    assert assignment.net_payable == Decimal("22000.00")
    assert assignment.outstanding_due == Decimal("22000.00")
    assert assignment.status == StudentFeeAssignmentStatus.PENDING

    # Duplicate assignment rejection
    with pytest.raises(AlreadyExistsException):
        fee_service.assign_fee_structure(db, assign_data, school.id)


def test_inactive_student_and_class_mismatch_rejected(db_session):
    db = db_session
    school = create_test_school(db, "Mismatch School", "MS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    sc1, sec1 = create_test_class_and_section(db, school.id, "Class 1")
    sc2, sec2 = create_test_class_and_section(db, school.id, "Class 2")
    parent = create_test_parent(db, school.id)

    student_inactive = create_test_student(
        db, school.id, academic_year_id=ay.id, school_class_id=sc1.id, section_id=sec1.id, parent_id=parent.id, status=StudentStatus.INACTIVE
    )

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        school_class_id=sc1.id,
        name="Class 1 Fee Structure",
        items=[],
    )
    structure = fee_service.create_fee_structure(db, struct_data, school.id)

    # Inactive student assignment rejection
    assign_inactive = StudentFeeAssignmentCreate(
        academic_year_id=ay.id,
        student_id=student_inactive.id,
        fee_structure_id=structure.id,
    )
    with pytest.raises(ValidationException):
        fee_service.assign_fee_structure(db, assign_inactive, school.id)

    # Class mismatch student rejection
    student_class2 = create_test_student(
        db, school.id, academic_year_id=ay.id, school_class_id=sc2.id, section_id=sec2.id, parent_id=parent.id
    )
    assign_class2 = StudentFeeAssignmentCreate(
        academic_year_id=ay.id,
        student_id=student_class2.id,
        fee_structure_id=structure.id,
    )
    with pytest.raises(ValidationException):
        fee_service.assign_fee_structure(db, assign_class2, school.id)


def test_discounts_and_custom_student_items(db_session):
    db = db_session
    school = create_test_school(db, "Discount School", "DS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        name="Base Fee Structure",
        items=[
            FeeItemCreate(
                category=FeeCategory.TUITION,
                name="Tuition",
                amount=Decimal("10000.00"),
            )
        ],
    )
    structure = fee_service.create_fee_structure(db, struct_data, school.id)

    assign_data = StudentFeeAssignmentCreate(
        academic_year_id=ay.id,
        student_id=student.id,
        fee_structure_id=structure.id,
    )
    assignment = fee_service.assign_fee_structure(db, assign_data, school.id)

    # Add custom transportation item for this student
    custom_item = StudentFeeItemCreate(
        category=FeeCategory.TRANSPORTATION,
        name="Route A Transportation",
        amount=Decimal("5000.00"),
        is_optional=True,
        is_applicable=True,
    )
    assignment_with_item = fee_service.add_student_fee_item(
        db, assignment.id, custom_item, school.id
    )
    assert assignment_with_item.gross_amount == Decimal("15000.00")

    # Add valid discount
    discount_data = FeeDiscountCreate(
        discount_type=DiscountType.SIBLING_CONCESSION,
        name="Sibling Concession",
        amount=Decimal("3000.00"),
    )
    assignment_with_discount = fee_service.add_discount(
        db, assignment.id, discount_data, school.id
    )
    assert assignment_with_discount.total_discounts == Decimal("3000.00")
    assert assignment_with_discount.net_payable == Decimal("12000.00")

    # Excessive discount (> gross_amount) rejection
    excessive_discount = FeeDiscountCreate(
        discount_type=DiscountType.SCHOLARSHIP,
        name="Huge Scholarship",
        amount=Decimal("20000.00"),
    )
    with pytest.raises(ValidationException):
        fee_service.add_discount(db, assignment.id, excessive_discount, school.id)


def test_payment_recording_receipt_generation_and_status(db_session):
    db = db_session
    school = create_test_school(db, "Payment School", "PS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        name="Full Fee Structure",
        items=[
            FeeItemCreate(
                category=FeeCategory.TUITION,
                name="Tuition",
                amount=Decimal("10000.00"),
            )
        ],
    )
    structure = fee_service.create_fee_structure(db, struct_data, school.id)

    assign_data = StudentFeeAssignmentCreate(
        academic_year_id=ay.id,
        student_id=student.id,
        fee_structure_id=structure.id,
    )
    assignment = fee_service.assign_fee_structure(db, assign_data, school.id)

    # Partial payment 1
    payment1_data = FeePaymentCreate(
        student_fee_assignment_id=assignment.id,
        amount=Decimal("4000.00"),
        payment_date=date(2026, 5, 10),
        payment_mode=PaymentMode.UPI,
        reference_number="UPI123456",
    )
    p1 = fee_service.record_payment(db, payment1_data, school.id)
    assert p1.receipt_number.startswith("REC-")
    assert p1.amount == Decimal("4000.00")

    updated_assignment = fee_service.get_assignment(db, assignment.id, school.id)
    assert updated_assignment.status == StudentFeeAssignmentStatus.PARTIALLY_PAID
    assert updated_assignment.total_paid == Decimal("4000.00")
    assert updated_assignment.outstanding_due == Decimal("6000.00")

    # Excessive payment (> outstanding_due) rejection
    excessive_payment = FeePaymentCreate(
        student_fee_assignment_id=assignment.id,
        amount=Decimal("10000.00"),
        payment_date=date(2026, 5, 11),
        payment_mode=PaymentMode.CASH,
    )
    with pytest.raises(ValidationException):
        fee_service.record_payment(db, excessive_payment, school.id)

    # Full final payment 2
    payment2_data = FeePaymentCreate(
        student_fee_assignment_id=assignment.id,
        amount=Decimal("6000.00"),
        payment_date=date(2026, 5, 15),
        payment_mode=PaymentMode.BANK_TRANSFER,
        reference_number="NEFT987654",
    )
    p2 = fee_service.record_payment(db, payment2_data, school.id)
    assert p2.receipt_number != p1.receipt_number

    final_assignment = fee_service.get_assignment(db, assignment.id, school.id)
    assert final_assignment.status == StudentFeeAssignmentStatus.PAID
    assert final_assignment.total_paid == Decimal("10000.00")
    assert final_assignment.outstanding_due == Decimal("0.00")

    # Receipt retrieval
    receipt = fee_service.get_receipt(db, p1.id, school.id)
    assert receipt.receipt_number == p1.receipt_number
    assert receipt.amount == Decimal("4000.00")
    assert receipt.total_paid == Decimal("10000.00")


def test_exact_decimal_calculations(db_session):
    db = db_session
    school = create_test_school(db, "Decimal School", "DEC1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        name="Decimal Fee Structure",
        items=[
            FeeItemCreate(
                category=FeeCategory.TUITION,
                name="Tuition",
                amount=Decimal("100.33"),
            ),
            FeeItemCreate(
                category=FeeCategory.BOOKS,
                name="Books",
                amount=Decimal("200.67"),
            ),
        ],
    )
    structure = fee_service.create_fee_structure(db, struct_data, school.id)

    assignment = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student.id,
            fee_structure_id=structure.id,
        ),
        school.id,
    )
    assert assignment.gross_amount == Decimal("301.00")

    # Add custom item with fraction
    fee_service.add_student_fee_item(
        db,
        assignment.id,
        StudentFeeItemCreate(
            category=FeeCategory.MISCELLANEOUS,
            name="Misc Charge",
            amount=Decimal("50.10"),
        ),
        school.id,
    )

    # Add discount with fraction
    updated_assignment = fee_service.add_discount(
        db,
        assignment.id,
        FeeDiscountCreate(
            discount_type=DiscountType.SPECIAL_DISCOUNT,
            name="Special Concession",
            amount=Decimal("20.05"),
        ),
        school.id,
    )

    assert updated_assignment.gross_amount == Decimal("351.10")
    assert updated_assignment.total_discounts == Decimal("20.05")
    assert updated_assignment.net_payable == Decimal("331.05")
    assert updated_assignment.outstanding_due == Decimal("331.05")
    assert isinstance(updated_assignment.gross_amount, Decimal)
    assert isinstance(updated_assignment.net_payable, Decimal)


def test_tenant_isolation_cross_school_fee_item_and_ay_mismatch(db_session):
    db = db_session
    school_a = create_test_school(db, "School Alpha", "SA1")
    school_b = create_test_school(db, "School Beta", "SB1")

    ay_a = create_test_academic_year(db, school_a.id, "2026-27")
    ay_b = create_test_academic_year(db, school_b.id, "2026-27")

    student_a = create_test_student(db, school_a.id, academic_year_id=ay_a.id)

    struct_a = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay_a.id,
            name="Structure A",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition A", amount=Decimal("5000.00"))
            ],
        ),
        school_a.id,
    )

    struct_b = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay_b.id,
            name="Structure B",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition B", amount=Decimal("6000.00"))
            ],
        ),
        school_b.id,
    )
    item_b_id = struct_b.items[0].id

    # 1. Academic Year mismatch during assignment
    with pytest.raises(ValidationException, match="Academic year"):
        fee_service.assign_fee_structure(
            db,
            StudentFeeAssignmentCreate(
                academic_year_id=ay_b.id,
                student_id=student_a.id,
                fee_structure_id=struct_a.id,
            ),
            school_a.id,
        )

    # 2. Cross-school custom fee_item_id during assignment
    with pytest.raises(ValidationException, match="Custom fee item does not belong"):
        fee_service.assign_fee_structure(
            db,
            StudentFeeAssignmentCreate(
                academic_year_id=ay_a.id,
                student_id=student_a.id,
                fee_structure_id=struct_a.id,
                custom_items=[
                    StudentFeeItemCreate(
                        fee_item_id=item_b_id,
                        category=FeeCategory.TRANSPORTATION,
                        name="Invalid Bus Fee",
                        amount=Decimal("1000.00"),
                    )
                ],
            ),
            school_a.id,
        )

    # 3. Cross-school custom fee_item_id added post-assignment
    assignment_a = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay_a.id,
            student_id=student_a.id,
            fee_structure_id=struct_a.id,
        ),
        school_a.id,
    )
    with pytest.raises(ValidationException, match="fee_item_id does not belong"):
        fee_service.add_student_fee_item(
            db,
            assignment_a.id,
            StudentFeeItemCreate(
                fee_item_id=item_b_id,
                category=FeeCategory.BOOKS,
                name="Invalid Books Fee",
                amount=Decimal("500.00"),
            ),
            school_a.id,
        )


def test_status_transitions_paid_to_partially_paid_and_discount_to_paid(db_session):
    db = db_session
    school = create_test_school(db, "Transition School", "TS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay.id,
            name="Base Structure",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition", amount=Decimal("10000.00"))
            ],
        ),
        school.id,
    )
    assignment = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student.id,
            fee_structure_id=struct.id,
        ),
        school.id,
    )

    # Pay full amount -> PAID
    fee_service.record_payment(
        db,
        FeePaymentCreate(
            student_fee_assignment_id=assignment.id,
            amount=Decimal("10000.00"),
            payment_date=date(2026, 5, 1),
            payment_mode=PaymentMode.CASH,
        ),
        school.id,
    )
    paid_assign = fee_service.get_assignment(db, assignment.id, school.id)
    assert paid_assign.status == StudentFeeAssignmentStatus.PAID

    # Add custom item ($2000) -> transitions back to PARTIALLY_PAID
    assign_after_item = fee_service.add_student_fee_item(
        db,
        assignment.id,
        StudentFeeItemCreate(
            category=FeeCategory.UNIFORM,
            name="Uniform Fee",
            amount=Decimal("2000.00"),
        ),
        school.id,
    )
    assert assign_after_item.status == StudentFeeAssignmentStatus.PARTIALLY_PAID
    assert assign_after_item.outstanding_due == Decimal("2000.00")

    # Apply discount ($2000) -> net payable reduces to $10000 -> transitions back to PAID
    assign_after_discount = fee_service.add_discount(
        db,
        assignment.id,
        FeeDiscountCreate(
            discount_type=DiscountType.SCHOLARSHIP,
            name="Uniform Waiver",
            amount=Decimal("2000.00"),
        ),
        school.id,
    )
    assert assign_after_discount.status == StudentFeeAssignmentStatus.PAID
    assert assign_after_discount.outstanding_due == Decimal("0.00")


def test_cancelled_assignment_payment_rejected(db_session):
    db = db_session
    school = create_test_school(db, "Cancelled School", "CS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay.id,
            name="Structure C",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition", amount=Decimal("5000.00"))
            ],
        ),
        school.id,
    )
    assignment_res = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student.id,
            fee_structure_id=struct.id,
        ),
        school.id,
    )

    # Manually set status to CANCELLED for testing invariant
    assignment = db.query(StudentFeeAssignment).filter_by(id=assignment_res.id).first()
    assignment.status = StudentFeeAssignmentStatus.CANCELLED
    db.commit()

    # Attempt payment -> raises ValidationException
    payment_data = FeePaymentCreate(
        student_fee_assignment_id=assignment.id,
        amount=Decimal("1000.00"),
        payment_date=date(2026, 5, 1),
        payment_mode=PaymentMode.CASH,
    )
    with pytest.raises(ValidationException, match="Cannot record payment for a cancelled fee assignment"):
        fee_service.record_payment(db, payment_data, school.id)


def test_delete_assignment_with_active_payments_rejected(db_session):
    db = db_session
    school = create_test_school(db, "Protect History School", "PH1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay.id,
            name="Structure P",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition", amount=Decimal("5000.00"))
            ],
        ),
        school.id,
    )
    assignment = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student.id,
            fee_structure_id=struct.id,
        ),
        school.id,
    )

    fee_service.record_payment(
        db,
        FeePaymentCreate(
            student_fee_assignment_id=assignment.id,
            amount=Decimal("1000.00"),
            payment_date=date(2026, 5, 1),
            payment_mode=PaymentMode.UPI,
        ),
        school.id,
    )

    with pytest.raises(ValidationException, match="Cannot delete student fee assignment with active payment records"):
        fee_service.delete_assignment(db, assignment.id, school.id)


def test_fee_structure_uniqueness_null_school_class_id(db_session):
    db = db_session
    school = create_test_school(db, "Null Class School", "NCS1")
    ay = create_test_academic_year(db, school.id, "2026-27")

    struct_data = FeeStructureCreate(
        academic_year_id=ay.id,
        school_class_id=None,
        name="School Wide Fees",
        items=[],
    )

    s1 = fee_service.create_fee_structure(db, struct_data, school.id)
    assert s1.id is not None

    with pytest.raises(AlreadyExistsException):
        fee_service.create_fee_structure(db, struct_data, school.id)


def test_add_duplicate_discount_type_rejected(db_session):
    db = db_session
    school = create_test_school(db, "Dup Discount School", "DDS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay.id,
            name="Fee Structure Dup Discount",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition", amount=Decimal("10000.00"))
            ],
        ),
        school.id,
    )
    assignment = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student.id,
            fee_structure_id=struct.id,
        ),
        school.id,
    )

    fee_service.add_discount(
        db,
        assignment.id,
        FeeDiscountCreate(
            discount_type=DiscountType.SIBLING_CONCESSION,
            name="Sibling Discount 1",
            amount=Decimal("1000.00"),
        ),
        school.id,
    )

    with pytest.raises(AlreadyExistsException):
        fee_service.add_discount(
            db,
            assignment.id,
            FeeDiscountCreate(
                discount_type=DiscountType.SIBLING_CONCESSION,
                name="Sibling Discount 2",
                amount=Decimal("500.00"),
            ),
            school.id,
        )


def test_remove_discount_and_recalculate_status(db_session):
    db = db_session
    school = create_test_school(db, "Remove Discount School", "RDS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay.id,
            name="Fee Structure Remove Discount",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition", amount=Decimal("10000.00"))
            ],
        ),
        school.id,
    )
    assignment = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student.id,
            fee_structure_id=struct.id,
        ),
        school.id,
    )

    # Add discount of 2000
    res1 = fee_service.add_discount(
        db,
        assignment.id,
        FeeDiscountCreate(
            discount_type=DiscountType.SCHOLARSHIP,
            name="Merit Scholarship",
            amount=Decimal("2000.00"),
        ),
        school.id,
    )
    discount_id = res1.discounts[0].id

    # Pay remaining balance of 8000 -> status is PAID
    fee_service.record_payment(
        db,
        FeePaymentCreate(
            student_fee_assignment_id=assignment.id,
            amount=Decimal("8000.00"),
            payment_date=date(2026, 5, 1),
            payment_mode=PaymentMode.CASH,
        ),
        school.id,
    )
    paid_assignment = fee_service.get_assignment(db, assignment.id, school.id)
    assert paid_assignment.status == StudentFeeAssignmentStatus.PAID

    # Remove discount -> net payable increases to 10000, paid is 8000 -> status becomes PARTIALLY_PAID
    res_after_remove = fee_service.remove_discount(
        db, assignment.id, discount_id, school.id
    )
    assert res_after_remove.status == StudentFeeAssignmentStatus.PARTIALLY_PAID
    assert res_after_remove.outstanding_due == Decimal("2000.00")
    assert len(res_after_remove.discounts) == 0


def test_cancel_assignment_success_and_validations(db_session):
    db = db_session
    school = create_test_school(db, "Cancel Assignment School", "CAS1")
    ay = create_test_academic_year(db, school.id, "2026-27")
    student = create_test_student(db, school.id, academic_year_id=ay.id)

    struct = fee_service.create_fee_structure(
        db,
        FeeStructureCreate(
            academic_year_id=ay.id,
            name="Fee Structure Cancel",
            items=[
                FeeItemCreate(category=FeeCategory.TUITION, name="Tuition", amount=Decimal("10000.00"))
            ],
        ),
        school.id,
    )
    assignment = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student.id,
            fee_structure_id=struct.id,
        ),
        school.id,
    )

    # 1. Successful cancellation
    cancelled = fee_service.cancel_assignment(db, assignment.id, school.id)
    assert cancelled.status == StudentFeeAssignmentStatus.CANCELLED

    # 2. Re-cancelling already cancelled assignment fails
    with pytest.raises(ValidationException, match="Assignment is already cancelled"):
        fee_service.cancel_assignment(db, assignment.id, school.id)

    # 3. Cancelling assignment with active payments fails
    student2 = create_test_student(db, school.id, academic_year_id=ay.id)
    assignment2 = fee_service.assign_fee_structure(
        db,
        StudentFeeAssignmentCreate(
            academic_year_id=ay.id,
            student_id=student2.id,
            fee_structure_id=struct.id,
        ),
        school.id,
    )
    fee_service.record_payment(
        db,
        FeePaymentCreate(
            student_fee_assignment_id=assignment2.id,
            amount=Decimal("1000.00"),
            payment_date=date(2026, 5, 1),
            payment_mode=PaymentMode.CASH,
        ),
        school.id,
    )
    with pytest.raises(ValidationException, match="Cannot cancel fee assignment with active payment records"):
        fee_service.cancel_assignment(db, assignment2.id, school.id)
