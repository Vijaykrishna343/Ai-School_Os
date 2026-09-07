import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.enums.visitor import HostType, IdProofType, VisitorStatus
from app.database.common_model import CommonModel
from app.models.school.school import School
from app.models.visitor.visitor import Visitor
from app.schemas.visitor import (
    VisitorCreate,
    VisitorListResponse,
    VisitorResponse,
    VisitorSummaryResponse,
)


@pytest.fixture(autouse=True)
def setup_visitor_db_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    yield


@pytest.fixture
def visitor_fixture(db_session):
    school_a = School(
        id=uuid.uuid4(),
        name="Visitor Test School A",
        code=f"VSA-{uuid.uuid4().hex[:4]}",
        address_line1="100 Visitor Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    school_b = School(
        id=uuid.uuid4(),
        name="Visitor Test School B",
        code=f"VSB-{uuid.uuid4().hex[:4]}",
        address_line1="200 Visitor Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()
    return {"school_a": school_a, "school_b": school_b}


def test_visitor_creation_and_defaults(db_session, visitor_fixture):
    school_a = visitor_fixture["school_a"]

    visitor = Visitor(
        school_id=school_a.id,
        visitor_name="John Doe",
        phone="9876543210",
        purpose="Parent Teacher Meeting",
        status=VisitorStatus.CHECKED_IN,
        pass_number="PASS-1001",
    )
    db_session.add(visitor)
    db_session.commit()

    assert visitor.id is not None
    assert visitor.visitor_name == "John Doe"
    assert visitor.phone == "9876543210"
    assert visitor.purpose == "Parent Teacher Meeting"
    assert visitor.status == VisitorStatus.CHECKED_IN
    assert visitor.pass_number == "PASS-1001"
    assert visitor.is_deleted is False
    assert visitor.created_at is not None


def test_visitor_enum_validation(db_session, visitor_fixture):
    school_a = visitor_fixture["school_a"]

    visitor = Visitor(
        school_id=school_a.id,
        visitor_name="Jane Smith",
        phone="9123456789",
        email="jane.smith@example.com",
        id_proof_type=IdProofType.AADHAAR,
        id_proof_number="1234-5678-9012",
        purpose="Vendor Meeting",
        host_type=HostType.STAFF,
        host_id=uuid.uuid4(),
        status=VisitorStatus.EXPECTED,
    )
    db_session.add(visitor)
    db_session.commit()

    assert visitor.id_proof_type == IdProofType.AADHAAR
    assert visitor.host_type == HostType.STAFF
    assert visitor.status == VisitorStatus.EXPECTED


def test_visitor_tenant_isolation_and_scoping(db_session, visitor_fixture):
    school_a = visitor_fixture["school_a"]
    school_b = visitor_fixture["school_b"]

    v_a = Visitor(
        school_id=school_a.id,
        visitor_name="School A Visitor",
        phone="9000000001",
        purpose="Inspection",
    )
    v_b = Visitor(
        school_id=school_b.id,
        visitor_name="School B Visitor",
        phone="9000000002",
        purpose="Audit",
    )
    db_session.add_all([v_a, v_b])
    db_session.commit()

    # Query School A
    res_a = db_session.scalars(
        select(Visitor).where(Visitor.school_id == school_a.id, Visitor.is_deleted == False)
    ).all()
    assert len(res_a) == 1
    assert res_a[0].visitor_name == "School A Visitor"

    # Query School B
    res_b = db_session.scalars(
        select(Visitor).where(Visitor.school_id == school_b.id, Visitor.is_deleted == False)
    ).all()
    assert len(res_b) == 1
    assert res_b[0].visitor_name == "School B Visitor"


def test_visitor_tenant_pass_number_uniqueness(db_session, visitor_fixture):
    school_a = visitor_fixture["school_a"]
    school_b = visitor_fixture["school_b"]

    # Same pass number in DIFFERENT schools is allowed
    v_a = Visitor(
        school_id=school_a.id,
        visitor_name="Visitor A",
        phone="9000000011",
        purpose="Visit A",
        pass_number="PASS-999",
    )
    v_b = Visitor(
        school_id=school_b.id,
        visitor_name="Visitor B",
        phone="9000000012",
        purpose="Visit B",
        pass_number="PASS-999",
    )
    db_session.add_all([v_a, v_b])
    db_session.commit()

    # Duplicate pass number within SAME school raises constraint error
    v_a_dup = Visitor(
        school_id=school_a.id,
        visitor_name="Visitor A Dup",
        phone="9000000013",
        purpose="Visit A Dup",
        pass_number="PASS-999",
    )
    db_session.add(v_a_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_visitor_pydantic_schema_validation(visitor_fixture):
    school_a = visitor_fixture["school_a"]

    # Valid payload
    create_dto = VisitorCreate(
        visitor_name="Schema User",
        phone="9876543210",
        purpose="Delivery",
        id_proof_type=IdProofType.PAN,
        id_proof_number="ABCDE1234F",
    )
    assert create_dto.visitor_name == "Schema User"
    assert create_dto.id_proof_type == IdProofType.PAN

    # Missing required field
    with pytest.raises(ValidationError):
        VisitorCreate(phone="9876543210", purpose="Delivery")

    # Detailed Response exposes id_proof_number
    dummy_now = datetime.now(timezone.utc)
    detail_resp = VisitorResponse(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_name="Detail User",
        phone="9876543210",
        email=None,
        id_proof_type=IdProofType.PAN,
        id_proof_number="ABCDE1234F",
        purpose="Delivery",
        host_type=None,
        host_id=None,
        check_in_time=dummy_now,
        check_out_time=None,
        status=VisitorStatus.CHECKED_IN,
        pass_number="PASS-101",
        remarks=None,
        created_at=dummy_now,
        updated_at=dummy_now,
    )
    assert detail_resp.id_proof_number == "ABCDE1234F"

    # Privacy Summary Response omits id_proof_number for privacy protection
    summary_resp = VisitorSummaryResponse(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_name="Summary User",
        phone="9876543210",
        email=None,
        id_proof_type=IdProofType.PAN,
        purpose="Delivery",
        host_type=None,
        host_id=None,
        check_in_time=dummy_now,
        check_out_time=None,
        status=VisitorStatus.CHECKED_IN,
        pass_number="PASS-101",
        created_at=dummy_now,
        updated_at=dummy_now,
    )
    assert not hasattr(summary_resp, "id_proof_number")
