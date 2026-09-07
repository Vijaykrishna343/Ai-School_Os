import uuid
from datetime import date, datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.common.enums.visitor import HostType, ReceptionInquiryStatus, VisitorStatus
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.school.school import School
from app.models.visitor.reception_inquiry import ReceptionInquiry
from app.models.visitor.visitor import Visitor


@pytest.fixture(autouse=True)
def setup_analytics_api_tables(db_session):
    import app.models  # Load mapped models in SQLAlchemy registry
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def analytics_api_fixture(db_session):
    uid_suffix = uuid.uuid4().hex[:6]

    # School A
    school_a = School(
        id=uuid.uuid4(),
        name=f"Analytics School A {uid_suffix}",
        code=f"ASA-{uid_suffix[:4]}",
        address_line1="100 Analytics Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B
    school_b = School(
        id=uuid.uuid4(),
        name=f"Analytics School B {uid_suffix}",
        code=f"ASB-{uid_suffix[:4]}",
        address_line1="200 Analytics Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500002",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    role_admin = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Super Admin")
    role_student = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Student")
    db_session.add_all([role_admin, role_student])
    db_session.flush()

    # Users
    user_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"reception_a_{uid_suffix}@analytics.test",
        username=f"user_a_{uid_suffix}",
        first_name="User",
        last_name="A",
        password_hash="hashed_pw",
        is_active=True,
    )
    user_a.roles.append(role_admin)

    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email=f"reception_b_{uid_suffix}@analytics.test",
        username=f"user_b_{uid_suffix}",
        first_name="User",
        last_name="B",
        password_hash="hashed_pw",
        is_active=True,
    )
    user_b.roles.append(role_admin)

    user_unauth = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"unauth_{uid_suffix}@analytics.test",
        username=f"user_unauth_{uid_suffix}",
        first_name="User",
        last_name="Unauth",
        password_hash="hashed_pw",
        is_active=True,
    )
    user_unauth.roles.append(role_student)

    db_session.add_all([user_a, user_b, user_unauth])
    db_session.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "user_a": user_a,
        "user_b": user_b,
        "user_unauth": user_unauth,
    }


def test_get_analytics_unauthenticated():
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(fastapi_app)
    res = client.get("/api/v1/reception/analytics")
    assert res.status_code == 401


def test_get_analytics_rbac_denial(analytics_api_fixture):
    user_unauth = analytics_api_fixture["user_unauth"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_unauth
    client = TestClient(fastapi_app)

    res = client.get("/api/v1/reception/analytics")
    assert res.status_code == 403


def test_get_analytics_invalid_date_range(analytics_api_fixture):
    user_a = analytics_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    # start_date > end_date
    res = client.get("/api/v1/reception/analytics?start_date=2026-09-10&end_date=2026-09-01")
    assert res.status_code == 400
    assert "start_date must be less than or equal to end_date" in str(res.json())

    # Exceeding 365 days
    res = client.get("/api/v1/reception/analytics?start_date=2024-01-01&end_date=2026-09-01")
    assert res.status_code == 400
    assert "Date range cannot exceed 365 days" in str(res.json())


def test_get_analytics_empty_period(analytics_api_fixture):
    user_a = analytics_api_fixture["user_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    res = client.get("/api/v1/reception/analytics?start_date=2026-01-01&end_date=2026-01-07")
    assert res.status_code == 200
    data = res.json()

    assert data["period"]["start_date"] == "2026-01-01"
    assert data["period"]["end_date"] == "2026-01-07"
    assert data["visitors"]["total"] == 0
    assert data["visitors"]["checked_in"] == 0
    assert data["visitors"]["checked_out"] == 0
    assert data["visitors"]["currently_active"] == 0
    assert data["inquiries"]["total"] == 0
    assert data["inquiries"]["pending"] == 0
    assert data["appointments"]["total"] == 0
    assert data["operational_metrics"]["avg_visitor_duration_minutes"] is None
    assert data["operational_metrics"]["peak_checkin_hour"] is None
    assert len(data["visitor_trend"]) == 7
    assert all(item["count"] == 0 for item in data["visitor_trend"])


def test_get_analytics_success_and_metrics(analytics_api_fixture, db_session):
    user_a = analytics_api_fixture["user_a"]
    school_a = analytics_api_fixture["school_a"]

    now = datetime.now()
    t_checkin1 = now - timedelta(hours=3)
    t_checkout1 = now - timedelta(hours=1)
    t_checkin2 = now - timedelta(hours=2)

    # 1. Visitor checked out (duration 120 mins)
    v1 = Visitor(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_name="John Doe",
        phone="9876543210",
        purpose="Parent Meeting",
        host_type=HostType.TEACHER,
        status=VisitorStatus.CHECKED_OUT,
        check_in_time=t_checkin1,
        check_out_time=t_checkout1,
        pass_number="PASS-1001",
    )
    # 2. Visitor active right now
    v2 = Visitor(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_name="Jane Smith",
        phone="9876543211",
        purpose="Fee Payment",
        host_type=HostType.STAFF,
        status=VisitorStatus.CHECKED_IN,
        check_in_time=t_checkin2,
        pass_number="PASS-1002",
    )
    db_session.add_all([v1, v2])

    # 3. Reception Inquiries
    inq1 = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=school_a.id,
        contact_name="Alice Brown",
        contact_phone="9876543212",
        subject="Admission Inquiry",
        status=ReceptionInquiryStatus.PENDING,
        appointment_time=now + timedelta(days=2),
    )
    inq2 = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=school_a.id,
        contact_name="Bob Green",
        contact_phone="9876543213",
        subject="Document Submission",
        status=ReceptionInquiryStatus.RESOLVED,
    )
    db_session.add_all([inq1, inq2])
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    today_str = date.today().isoformat()
    res = client.get(f"/api/v1/reception/analytics?start_date={today_str}&end_date={today_str}")
    assert res.status_code == 200
    data = res.json()

    # Visitor counts
    assert data["visitors"]["total"] == 2
    assert data["visitors"]["checked_in"] == 1
    assert data["visitors"]["checked_out"] == 1
    assert data["visitors"]["currently_active"] == 1

    # Inquiry counts
    assert data["inquiries"]["total"] == 2
    assert data["inquiries"]["pending"] == 1
    assert data["inquiries"]["resolved"] == 1

    # Appointment counts
    assert data["appointments"]["total"] == 1
    assert data["appointments"]["upcoming"] == 1

    # Operational metrics
    assert data["operational_metrics"]["avg_visitor_duration_minutes"] == 120.0
    assert data["operational_metrics"]["peak_checkin_hour"] == t_checkin1.hour
    assert len(data["operational_metrics"]["visitors_by_purpose"]) > 0
    assert len(data["operational_metrics"]["visitors_by_host_type"]) > 0


def test_get_analytics_tenant_isolation(analytics_api_fixture, db_session):
    school_a = analytics_api_fixture["school_a"]
    school_b = analytics_api_fixture["school_b"]
    user_b = analytics_api_fixture["user_b"]

    now = datetime.now()

    # School A record
    v_a = Visitor(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_name="School A Visitor",
        phone="9999999999",
        purpose="Meeting A",
        status=VisitorStatus.CHECKED_IN,
        check_in_time=now,
        pass_number="PASS-A",
    )
    # School B record
    v_b = Visitor(
        id=uuid.uuid4(),
        school_id=school_b.id,
        visitor_name="School B Visitor",
        phone="8888888888",
        purpose="Meeting B",
        status=VisitorStatus.CHECKED_IN,
        check_in_time=now,
        pass_number="PASS-B",
    )
    db_session.add_all([v_a, v_b])
    db_session.commit()

    # User B queries analytics -> should ONLY see School B visitor metrics
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_b
    client = TestClient(fastapi_app)

    today_str = date.today().isoformat()
    res = client.get(f"/api/v1/reception/analytics?start_date={today_str}&end_date={today_str}")
    assert res.status_code == 200
    data = res.json()

    assert data["visitors"]["total"] == 1
    assert data["visitors"]["currently_active"] == 1


def test_get_analytics_soft_deleted_exclusion(analytics_api_fixture, db_session):
    school_a = analytics_api_fixture["school_a"]
    user_a = analytics_api_fixture["user_a"]

    now = datetime.now()

    v_deleted = Visitor(
        id=uuid.uuid4(),
        school_id=school_a.id,
        visitor_name="Deleted Visitor",
        phone="7777777777",
        purpose="Deleted Meeting",
        status=VisitorStatus.CHECKED_IN,
        check_in_time=now,
        pass_number="PASS-DEL",
        is_deleted=True,
    )
    inq_deleted = ReceptionInquiry(
        id=uuid.uuid4(),
        school_id=school_a.id,
        contact_name="Deleted Inquiry",
        contact_phone="7777777777",
        subject="Deleted Subject",
        status=ReceptionInquiryStatus.PENDING,
        is_deleted=True,
    )
    db_session.add_all([v_deleted, inq_deleted])
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a
    client = TestClient(fastapi_app)

    today_str = date.today().isoformat()
    res = client.get(f"/api/v1/reception/analytics?start_date={today_str}&end_date={today_str}")
    assert res.status_code == 200
    data = res.json()

    assert data["visitors"]["total"] == 0
    assert data["visitors"]["currently_active"] == 0
    assert data["inquiries"]["total"] == 0
