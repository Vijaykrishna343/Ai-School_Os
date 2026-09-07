import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.enums import Gender, StudentStatus
from app.common.enums.fees import FeeCategory, FeeStructureStatus, PaymentMode, StudentFeeAssignmentStatus
from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus
from app.models.academic_year.academic_year import AcademicYear
from app.models.fees.fee_structure import FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.parent.parent import Parent
from app.models.payment.payment_order import PaymentOrder
from app.models.payment.payment_transaction import PaymentTransaction
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student


def create_sample_school(db_session: Session, name: str = "Payment Test School") -> School:
    school = School(
        name=name,
        code=f"PTS-{uuid.uuid4().hex[:6]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()
    return school


@pytest.fixture(autouse=True)
def setup_payment_tables(db_session: Session):
    from app.database.common_model import CommonModel
    CommonModel.metadata.create_all(db_session.get_bind())



def create_sample_student_fee_assignment(db_session: Session, school: School) -> StudentFeeAssignment:
    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    db_session.add(ay)
    db_session.commit()

    sclass = SchoolClass(
        school_id=school.id,
        name=f"Class {uuid.uuid4().hex[:4]}",
        display_order=1,
    )
    db_session.add(sclass)
    db_session.commit()

    section = Section(
        school_class_id=sclass.id,
        name="Section A",
    )
    db_session.add(section)
    db_session.commit()

    parent = Parent(
        school_id=school.id,
        father_name="Father John",
        primary_phone=f"9876{uuid.uuid4().hex[:6]}",
        address_line1="123 Street",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(parent)
    db_session.commit()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number=f"R-{uuid.uuid4().hex[:4]}",
        first_name="John",
        last_name="Doe",
        gender=Gender.MALE,
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2025, 4, 1),
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add(student)
    db_session.commit()

    fee_structure = FeeStructure(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Standard Fee Structure",
        status=FeeStructureStatus.ACTIVE,
    )
    db_session.add(fee_structure)
    db_session.commit()

    assignment = StudentFeeAssignment(
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student.id,
        fee_structure_id=fee_structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 9, 30),
    )
    db_session.add(assignment)
    db_session.commit()
    return assignment


def test_payment_order_creation(db_session: Session):
    school = create_sample_school(db_session)
    assignment = create_sample_student_fee_assignment(db_session, school)

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_{uuid.uuid4().hex[:12]}",
        amount=Decimal("15000.50"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
        extra_metadata={"notes": "Term 1 fee checkout"},
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert saved_order is not None
    assert saved_order.school_id == school.id
    assert saved_order.student_fee_assignment_id == assignment.id
    assert saved_order.provider == PaymentProvider.RAZORPAY
    assert saved_order.amount == Decimal("15000.50")
    assert saved_order.currency == "INR"
    assert saved_order.status == PaymentOrderStatus.CREATED
    assert saved_order.extra_metadata == {"notes": "Term 1 fee checkout"}
    assert saved_order.is_deleted is False


def test_payment_transaction_creation_and_relationship(db_session: Session):
    school = create_sample_school(db_session)
    assignment = create_sample_student_fee_assignment(db_session, school)

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.STRIPE,
        gateway_order_id=f"cs_{uuid.uuid4().hex[:12]}",
        amount=Decimal("5000.00"),
        status=PaymentOrderStatus.PENDING,
    )
    db_session.add(order)
    db_session.commit()

    transaction = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.STRIPE,
        gateway_transaction_id=f"pi_{uuid.uuid4().hex[:12]}",
        gateway_event_id=f"evt_{uuid.uuid4().hex[:12]}",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("5000.00"),
        payment_method="card",
        event_timestamp=datetime.now(timezone.utc),
        raw_response={"status": "succeeded"},
    )
    db_session.add(transaction)
    db_session.commit()

    saved_txn = db_session.query(PaymentTransaction).filter_by(id=transaction.id).first()
    assert saved_txn is not None
    assert saved_txn.order.id == order.id
    assert saved_txn.order.assignment.id == assignment.id
    assert len(order.transactions) == 1
    assert order.transactions[0].id == transaction.id


def test_payment_multi_tenant_isolation(db_session: Session):
    school_a = create_sample_school(db_session, name="School A")
    school_b = create_sample_school(db_session, name="School B")

    assignment_a = create_sample_student_fee_assignment(db_session, school_a)
    assignment_b = create_sample_student_fee_assignment(db_session, school_b)

    order_a = PaymentOrder(
        school_id=school_a.id,
        student_fee_assignment_id=assignment_a.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_a_{uuid.uuid4().hex[:8]}",
        amount=Decimal("2000.00"),
    )
    order_b = PaymentOrder(
        school_id=school_b.id,
        student_fee_assignment_id=assignment_b.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_b_{uuid.uuid4().hex[:8]}",
        amount=Decimal("3000.00"),
    )
    db_session.add_all([order_a, order_b])
    db_session.commit()

    orders_for_a = db_session.query(PaymentOrder).filter(PaymentOrder.school_id == school_a.id).all()
    assert len(orders_for_a) == 1
    assert orders_for_a[0].id == order_a.id

    orders_for_b = db_session.query(PaymentOrder).filter(PaymentOrder.school_id == school_b.id).all()
    assert len(orders_for_b) == 1
    assert orders_for_b[0].id == order_b.id


def test_payment_transaction_idempotency_unique_constraint(db_session: Session):
    school = create_sample_school(db_session)
    assignment = create_sample_student_fee_assignment(db_session, school)

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_{uuid.uuid4().hex[:8]}",
        amount=Decimal("1000.00"),
    )
    db_session.add(order)
    db_session.commit()

    gateway_txn_id = f"pay_{uuid.uuid4().hex[:10]}"

    txn1 = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id=gateway_txn_id,
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("1000.00"),
    )
    db_session.add(txn1)
    db_session.commit()

    # Attempting to insert a duplicate transaction with the same provider & gateway_transaction_id must fail
    txn2 = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id=gateway_txn_id,
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("1000.00"),
    )
    db_session.add(txn2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_financial_monetary_decimal_precision(db_session: Session):
    school = create_sample_school(db_session)
    assignment = create_sample_student_fee_assignment(db_session, school)

    exact_amount = Decimal("1234567.89")
    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_{uuid.uuid4().hex[:8]}",
        amount=exact_amount,
    )
    db_session.add(order)
    db_session.commit()

    saved_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert isinstance(saved_order.amount, Decimal)
    assert saved_order.amount == exact_amount
