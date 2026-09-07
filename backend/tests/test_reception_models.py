import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.common.enums.visitor import HostType, ReceptionInquiryStatus
from app.database.common_model import CommonModel
from app.models.school.school import School
from app.models.visitor.reception_inquiry import ReceptionInquiry
from app.models.visitor.visitor import Visitor
from app.schemas.visitor import (
    ReceptionInquiryCreate,
    ReceptionInquiryListResponse,
    ReceptionInquiryResponse,
)


@pytest.fixture(autouse=True)
def setup_reception_db_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    yield


@pytest.fixture
def reception_fixture(db_session):
    school_a = School(
        id=uuid.uuid4(),
        name="Reception Test School A",
        code=f"RSA-{uuid.uuid4().hex[:4]}",
        address_line1="100 Desk St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    school_b = School(
        id=uuid.uuid4(),
        name="Reception Test School B",
        code=f"RSB-{uuid.uuid4().hex[:4]}",
        address_line1="200 Desk St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    visitor_a = Visitor(
        school_id=school_a.id,
        visitor_name="Alice Visitor",
        phone="9876543210",
        purpose="Inquiry",
    )
    db_session.add(visitor_a)
    db_session.commit()

    return {"school_a": school_a, "school_b": school_b, "visitor_a": visitor_a}


def test_reception_inquiry_creation_and_defaults(db_session, reception_fixture):
    school_a = reception_fixture["school_a"]
    visitor_a = reception_fixture["visitor_a"]

    inquiry = ReceptionInquiry(
        school_id=school_a.id,
        visitor_id=visitor_a.id,
        contact_name="Alice Visitor",
        contact_phone="9876543210",
        subject="Admission Information for Grade 1",
        details="Inquiring about fee structure and transport facilities.",
        status=ReceptionInquiryStatus.PENDING,
    )
    db_session.add(inquiry)
    db_session.commit()

    assert inquiry.id is not None
    assert inquiry.school_id == school_a.id
    assert inquiry.visitor_id == visitor_a.id
    assert inquiry.subject == "Admission Information for Grade 1"
    assert inquiry.status == ReceptionInquiryStatus.PENDING
    assert inquiry.visitor is not None
    assert inquiry.visitor.visitor_name == "Alice Visitor"


def test_reception_inquiry_enum_validation(db_session, reception_fixture):
    school_a = reception_fixture["school_a"]

    inquiry = ReceptionInquiry(
        school_id=school_a.id,
        contact_name="Bob Contact",
        contact_phone="9123456789",
        subject="Career Counseling Appointment",
        host_type=HostType.TEACHER,
        host_id=uuid.uuid4(),
        status=ReceptionInquiryStatus.IN_PROGRESS,
    )
    db_session.add(inquiry)
    db_session.commit()

    assert inquiry.host_type == HostType.TEACHER
    assert inquiry.status == ReceptionInquiryStatus.IN_PROGRESS


def test_reception_inquiry_tenant_isolation(db_session, reception_fixture):
    school_a = reception_fixture["school_a"]
    school_b = reception_fixture["school_b"]

    inq_a = ReceptionInquiry(
        school_id=school_a.id,
        contact_name="Contact A",
        contact_phone="9000000001",
        subject="Subject A",
    )
    inq_b = ReceptionInquiry(
        school_id=school_b.id,
        contact_name="Contact B",
        contact_phone="9000000002",
        subject="Subject B",
    )
    db_session.add_all([inq_a, inq_b])
    db_session.commit()

    res_a = db_session.scalars(
        select(ReceptionInquiry).where(
            ReceptionInquiry.school_id == school_a.id,
            ReceptionInquiry.is_deleted == False,
        )
    ).all()
    assert len(res_a) == 1
    assert res_a[0].contact_name == "Contact A"

    res_b = db_session.scalars(
        select(ReceptionInquiry).where(
            ReceptionInquiry.school_id == school_b.id,
            ReceptionInquiry.is_deleted == False,
        )
    ).all()
    assert len(res_b) == 1
    assert res_b[0].contact_name == "Contact B"


def test_reception_inquiry_pydantic_schemas(reception_fixture):
    school_a = reception_fixture["school_a"]

    # Valid schema payload
    create_dto = ReceptionInquiryCreate(
        contact_name="Parent Inquiry",
        contact_phone="9876543210",
        subject="Transport Route",
        status=ReceptionInquiryStatus.PENDING,
    )
    assert create_dto.contact_name == "Parent Inquiry"
    assert create_dto.status == ReceptionInquiryStatus.PENDING

    # Missing required contact_phone
    with pytest.raises(ValidationError):
        ReceptionInquiryCreate(
            contact_name="Parent Inquiry",
            subject="Transport Route",
        )

    # Response schema check
    dummy_now = datetime.now(timezone.utc)
    inq_resp = ReceptionInquiryResponse(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_id=None,
        contact_name="Parent Inquiry",
        contact_phone="9876543210",
        contact_email="parent@example.com",
        subject="Transport Route",
        details="Route info",
        host_type=None,
        host_id=None,
        appointment_time=None,
        status=ReceptionInquiryStatus.RESOLVED,
        notes="Resolved via phone call",
        created_at=dummy_now,
        updated_at=dummy_now,
    )
    assert inq_resp.status == ReceptionInquiryStatus.RESOLVED
