"""
Phase 9 Tests — Import, Export, Notifications, Audit Logs
Tests for Phase 9.1, 9.4, 9.5, 9.7
"""
import io
import uuid
import csv
from datetime import date

import pytest
from fastapi.testclient import TestClient

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


def create_school_user_with_perms(db, perms: list[str]):
    """Helper: seed identity, create school, role with perms, user, return (school, headers)."""
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=f"Test School {uuid.uuid4().hex[:4]}",
        code=f"TST{uuid.uuid4().hex[:4].upper()}",
        address_line1="1 Test Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Phase 9 Test Role",
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
        email=f"test_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Pass123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, headers


def make_student_csv(rows: list[dict]) -> tuple[bytes, str]:
    """Create CSV bytes for student import."""
    fieldnames = ["first_name", "last_name", "gender", "date_of_birth", "admission_number"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8"), "students.csv"


def make_teacher_csv(rows: list[dict]) -> tuple[bytes, str]:
    fieldnames = ["first_name", "last_name", "email", "phone"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8"), "teachers.csv"


# ══════════════════════════════════════════════════════════════════
# Phase 9.1 — Import Tests
# ══════════════════════════════════════════════════════════════════

class TestDataImportCSV:

    def _setup_school_fixtures(self, db_session, school):
        """Create academic year, class, and section for the school."""
        from app.models.academic_year.academic_year import AcademicYear
        from app.models.school_class.school_class import SchoolClass
        from app.models.section.section import Section

        ay = AcademicYear(
            id=uuid.uuid4(),
            school_id=school.id,
            name="2026-2027",
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            is_current=True,
        )
        db_session.add(ay)
        db_session.flush()

        sc = SchoolClass(
            id=uuid.uuid4(),
            school_id=school.id,
            name="Grade 5",
            display_order=5,
        )
        db_session.add(sc)
        db_session.flush()

        sec = Section(
            id=uuid.uuid4(),
            school_id=school.id,
            school_class_id=sc.id,
            name="A",
        )
        db_session.add(sec)
        db_session.commit()
        return ay, sc, sec

    def _setup_academic_year(self, db_session, school):
        """Legacy helper — creates only academic year (for backward compat)."""
        from app.models.academic_year.academic_year import AcademicYear
        ay = AcademicYear(
            id=uuid.uuid4(),
            school_id=school.id,
            name="2026-2027",
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            is_current=True,
        )
        db_session.add(ay)
        db_session.commit()
        return ay

    def test_student_csv_import_success(self, client, db_session):
        """Valid student CSV should import successfully."""
        school, headers = create_school_user_with_perms(db_session, ["student.create"])
        self._setup_academic_year(db_session, school)

        content, filename = make_student_csv([
            {"first_name": "Arjun", "last_name": "Kumar", "gender": "MALE",
             "date_of_birth": "2010-05-15", "admission_number": "ADM9001"},
            {"first_name": "Priya", "last_name": "Sharma", "gender": "FEMALE",
             "date_of_birth": "2011-03-20", "admission_number": "ADM9002"},
        ])

        response = client.post(
            "/api/v1/import/students",
            files={"file": (filename, content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["inserted_rows"] == 2
        assert data["total_rows"] == 2
        assert data["invalid_rows"] == 0
        assert data["duplicate_rows"] == 0

    def test_student_csv_import_duplicate_skipped(self, client, db_session):
        """Duplicate admission number in second import should be skipped."""
        school, headers = create_school_user_with_perms(db_session, ["student.create"])
        self._setup_academic_year(db_session, school)

        content1, fname = make_student_csv([
            {"first_name": "Suresh", "last_name": "Reddy", "gender": "MALE",
             "admission_number": "DUPTEST001"},
        ])
        response1 = client.post(
            "/api/v1/import/students",
            files={"file": (fname, content1, "text/csv")},
            headers=headers,
        )
        assert response1.status_code == 200
        assert response1.json()["data"]["inserted_rows"] == 1

        # Second import with same admission number
        content2, fname2 = make_student_csv([
            {"first_name": "Suresh", "last_name": "Reddy", "gender": "MALE",
             "admission_number": "DUPTEST001"},
        ])
        response2 = client.post(
            "/api/v1/import/students",
            files={"file": (fname2, content2, "text/csv")},
            headers=headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()["data"]
        assert data2["duplicate_rows"] == 1
        assert data2["skipped_rows"] == 1
        assert data2["inserted_rows"] == 0

    def test_student_csv_invalid_row_gender(self, client, db_session):
        """Row with invalid gender should be counted as invalid."""
        _, headers = create_school_user_with_perms(db_session, ["student.create"])

        content, fname = make_student_csv([
            {"first_name": "Test", "last_name": "User", "gender": "UNKNOWN"},
        ])
        response = client.post(
            "/api/v1/import/students",
            files={"file": (fname, content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["invalid_rows"] == 1
        assert data["inserted_rows"] == 0
        assert len(data["errors"]) >= 1

    def test_student_csv_missing_required_column(self, client, db_session):
        """CSV missing required column should return error."""
        _, headers = create_school_user_with_perms(db_session, ["student.create"])

        # Only first_name, missing last_name and gender
        content = b"first_name,date_of_birth\nArjun,2010-01-01\n"
        response = client.post(
            "/api/v1/import/students",
            files={"file": ("students.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["errors"]) >= 1
        assert data["inserted_rows"] == 0

    def test_import_wrong_entity_type_rejected(self, client, db_session):
        """Unknown entity type should return 400."""
        _, headers = create_school_user_with_perms(db_session, ["student.create"])

        content = b"col1,col2\nval1,val2\n"
        response = client.post(
            "/api/v1/import/unknownentity",
            files={"file": ("data.csv", content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 400

    def test_import_without_auth_rejected(self, client, db_session):
        """Import without token should return 401."""
        content = b"first_name,last_name,gender\nTest,User,MALE\n"
        response = client.post(
            "/api/v1/import/students",
            files={"file": ("students.csv", content, "text/csv")},
        )
        assert response.status_code == 401

    def test_teacher_csv_import_success(self, client, db_session):
        """Valid teacher CSV should import successfully."""
        school, headers = create_school_user_with_perms(db_session, ["student.create", "teacher.create"])

        content, fname = make_teacher_csv([
            {"first_name": "Ramesh", "last_name": "Iyer", "email": f"ramesh_{uuid.uuid4().hex[:4]}@school.com"},
        ])
        response = client.post(
            "/api/v1/import/teachers",
            files={"file": (fname, content, "text/csv")},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["inserted_rows"] == 1

    def test_import_schema_endpoint(self, client, db_session):
        """Schema endpoint returns required/optional columns."""
        _, headers = create_school_user_with_perms(db_session, ["student.view"])

        response = client.get("/api/v1/import/schema/students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "required_columns" in data
        assert "optional_columns" in data
        assert "first_name" in data["required_columns"]

    def test_tenant_isolation_import(self, client, db_session):
        """School A's import should not affect School B."""
        school_a, headers_a = create_school_user_with_perms(db_session, ["student.create"])
        school_b, headers_b = create_school_user_with_perms(db_session, ["student.create"])
        self._setup_academic_year(db_session, school_a)
        self._setup_academic_year(db_session, school_b)

        # Import student for school A
        content, fname = make_student_csv([
            {"first_name": "IsoTest", "last_name": "SchoolA", "gender": "MALE",
             "admission_number": "ISO_A_001"},
        ])
        response_a = client.post(
            "/api/v1/import/students",
            files={"file": (fname, content, "text/csv")},
            headers=headers_a,
        )
        assert response_a.json()["data"]["inserted_rows"] == 1

        # Import student for school B (same admission number should be allowed)
        content2, fname2 = make_student_csv([
            {"first_name": "IsoTest", "last_name": "SchoolB", "gender": "FEMALE",
             "admission_number": "ISO_A_001"},  # Same number, different school
        ])
        response_b = client.post(
            "/api/v1/import/students",
            files={"file": (fname2, content2, "text/csv")},
            headers=headers_b,
        )
        # School B should be able to import since it's isolated
        assert response_b.json()["data"]["inserted_rows"] == 1


# ══════════════════════════════════════════════════════════════════
# Phase 9.4 — Export Tests
# ══════════════════════════════════════════════════════════════════

class TestDataExport:

    def test_export_students_returns_csv(self, client, db_session):
        """Student export should return CSV content-type."""
        _, headers = create_school_user_with_perms(db_session, ["student.export"])

        response = client.get("/api/v1/export/students", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_teachers_returns_csv(self, client, db_session):
        _, headers = create_school_user_with_perms(db_session, ["teacher.export"])

        response = client.get("/api/v1/export/teachers", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_parents_returns_csv(self, client, db_session):
        _, headers = create_school_user_with_perms(db_session, ["parent.export"])

        response = client.get("/api/v1/export/parents", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_attendance_returns_csv(self, client, db_session):
        _, headers = create_school_user_with_perms(db_session, ["attendance.export"])

        response = client.get("/api/v1/export/attendance", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_fees_returns_csv(self, client, db_session):
        _, headers = create_school_user_with_perms(db_session, ["fees.export"])

        response = client.get("/api/v1/export/fees", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_exam_results_returns_csv(self, client, db_session):
        _, headers = create_school_user_with_perms(db_session, ["marks.view"])

        response = client.get("/api/v1/export/exam-results", headers=headers)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_without_auth_rejected(self, client):
        response = client.get("/api/v1/export/students")
        assert response.status_code == 401

    def test_export_student_includes_headers(self, client, db_session):
        """Exported CSV should include expected header columns."""
        _, headers = create_school_user_with_perms(db_session, ["student.export"])

        response = client.get("/api/v1/export/students", headers=headers)
        assert response.status_code == 200
        content = response.text
        assert "first_name" in content
        assert "last_name" in content
        assert "admission_number" in content

    def test_export_attendance_includes_student_name_header(self, client, db_session):
        """Exported Attendance CSV should include 'Student Name' user-facing header (DEF-10-3)."""
        _, headers = create_school_user_with_perms(db_session, ["attendance.export"])

        response = client.get("/api/v1/export/attendance", headers=headers)
        assert response.status_code == 200
        content = response.text
        assert "Student Name" in content
        assert "admission_number" in content
        assert "date" in content



# ══════════════════════════════════════════════════════════════════
# Phase 9.5 — Notification Tests
# ══════════════════════════════════════════════════════════════════

class TestNotifications:

    def test_list_notifications_empty(self, client, db_session):
        """Empty notifications list should return success."""
        _, headers = create_school_user_with_perms(db_session, ["school.view"])

        response = client.get("/api/v1/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]

    def test_send_announcement_creates_notification(self, client, db_session):
        """Sending announcement should create a notification record."""
        _, headers = create_school_user_with_perms(db_session, ["school.view", "school.update"])

        payload = {
            "title": "School Closed Tomorrow",
            "message": "School will remain closed tomorrow due to maintenance.",
            "recipient_name": "All Parents",
            "recipient_contact": "9999999999",
            "channel": "IN_APP",
        }
        response = client.post("/api/v1/notifications/send", json=payload, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] in ("SENT", "PENDING", "QUEUED")

    def test_notification_templates_endpoint(self, client, db_session):
        """Templates endpoint should list all notification templates."""
        _, headers = create_school_user_with_perms(db_session, ["school.view"])

        response = client.get("/api/v1/notifications/templates", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "student_absent_alert" in data["data"]
        assert "fee_payment_received" in data["data"]

    def test_notification_without_auth_rejected(self, client):
        response = client.get("/api/v1/notifications")
        assert response.status_code == 401

    def test_notification_tenant_isolation(self, client, db_session):
        """School A notifications should not appear for School B."""
        _, headers_a = create_school_user_with_perms(db_session, ["school.view", "school.update"])
        _, headers_b = create_school_user_with_perms(db_session, ["school.view"])

        # Create notification for school A
        payload = {
            "title": "School A Announcement",
            "message": "This is a school A announcement.",
            "recipient_name": "Test Parent",
            "recipient_contact": "8888888888",
            "channel": "IN_APP",
        }
        client.post("/api/v1/notifications/send", json=payload, headers=headers_a)

        # School B should not see School A's notification
        response_b = client.get("/api/v1/notifications", headers=headers_b)
        assert response_b.status_code == 200
        items_b = response_b.json()["data"]["items"]
        for item in items_b:
            assert item["title"] != "School A Announcement"


# ══════════════════════════════════════════════════════════════════
# Phase 9.7 — Audit Log Tests
# ══════════════════════════════════════════════════════════════════

class TestAuditLogs:

    def test_list_audit_logs_empty(self, client, db_session):
        """Audit logs should return empty list for new school."""
        _, headers = create_school_user_with_perms(db_session, ["school.view"])

        response = client.get("/api/v1/audit-logs", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] == 0

    def test_audit_log_without_auth_rejected(self, client):
        response = client.get("/api/v1/audit-logs")
        assert response.status_code == 401

    def test_audit_log_pagination(self, client, db_session):
        """Audit log listing respects page and page_size query params."""
        _, headers = create_school_user_with_perms(db_session, ["school.view"])

        response = client.get("/api/v1/audit-logs?page=1&page_size=5", headers=headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_audit_log_tenant_isolation(self, client, db_session):
        """School A's audit logs should not appear for School B."""
        from app.models.audit_log import AuditLog

        school_a, headers_a = create_school_user_with_perms(db_session, ["school.view"])
        school_b, headers_b = create_school_user_with_perms(db_session, ["school.view"])

        # Manually write an audit log for school A
        log = AuditLog(
            school_id=school_a.id,
            user_email="admin@schoola.com",
            action="TEST_ACTION",
            module="test_module",
            status_code=200,
        )
        db_session.add(log)
        db_session.commit()

        # School B should not see it
        response_b = client.get("/api/v1/audit-logs", headers=headers_b)
        assert response_b.status_code == 200
        items = response_b.json()["data"]["items"]
        for item in items:
            assert item.get("action") != "TEST_ACTION"


# ══════════════════════════════════════════════════════════════════
# Notification Service Unit Tests
# ══════════════════════════════════════════════════════════════════

class TestNotificationService:

    def test_mock_provider_sends_in_app(self, db_session):
        """MockNotificationProvider should mark notification as SENT."""
        from app.services.notification_service import NotificationService
        from app.models.notification import NotificationStatus, NotificationRecipientType, NotificationChannel

        school = School(
            id=uuid.uuid4(),
            name="Notif Test School",
            code=f"NTS{uuid.uuid4().hex[:4].upper()}",
            address_line1="1 Notif Lane",
            city="Test City",
            district="Test",
            state="TS",
            country="India",
            postal_code="100001",
        )
        db_session.add(school)
        db_session.commit()

        svc = NotificationService()
        notif = svc.create_and_send(
            db=db_session,
            school_id=school.id,
            recipient_type=NotificationRecipientType.PARENT,
            recipient_name="Test Parent",
            recipient_contact="9000000001",
            channel=NotificationChannel.IN_APP,
            template_key="student_absent_alert",
            template_variables={"student_name": "Arjun", "date": "2026-08-18"},
        )
        db_session.commit()

        assert notif.id is not None
        assert notif.status == NotificationStatus.SENT
        assert notif.school_id == school.id
        assert "Arjun" in notif.body

    def test_render_template_substitution(self):
        from app.services.notification_service import render_template

        title, body = render_template(
            "fee_payment_received",
            {
                "amount": "5000",
                "student_name": "Meera",
                "date": "2026-08-01",
                "receipt_number": "REC-001",
            }
        )
        assert "Meera" in body
        assert "5000" in body
        assert "REC-001" in body

    def test_render_unknown_template_fallback(self):
        from app.services.notification_service import render_template

        title, body = render_template("nonexistent_template", {"message": "hello"})
        assert body == "hello"


# ══════════════════════════════════════════════════════════════════
# Import Service Unit Tests
# ══════════════════════════════════════════════════════════════════

class TestImportService:

    def test_parse_csv_bytes(self):
        from app.services.import_service import parse_csv_bytes

        csv_data = b"first_name,last_name,gender\nArjun,Kumar,MALE\nPriya,Sharma,FEMALE\n"
        rows = parse_csv_bytes(csv_data)
        assert len(rows) == 2
        assert rows[0]["first_name"] == "Arjun"
        assert rows[1]["gender"] == "FEMALE"

    def test_parse_csv_strips_whitespace(self):
        from app.services.import_service import parse_csv_bytes

        csv_data = b"  first_name  ,  last_name  \n  Arjun  ,  Kumar  \n"
        rows = parse_csv_bytes(csv_data)
        assert rows[0]["first_name"] == "Arjun"

    def test_parse_date_formats(self):
        from app.services.import_service import _parse_date

        assert _parse_date("2010-05-15") is not None
        assert _parse_date("15/05/2010") is not None
        assert _parse_date("15-05-2010") is not None
        assert _parse_date("invalid") is None
        assert _parse_date("") is None
        assert _parse_date(None) is None

    def test_import_empty_csv_error(self, db_session):
        from app.services.import_service import import_data

        school = School(
            id=uuid.uuid4(),
            name="Import Test School",
            code=f"ITS{uuid.uuid4().hex[:4].upper()}",
            address_line1="1 Import Lane",
            city="Import City",
            district="Test",
            state="TS",
            country="India",
            postal_code="100001",
        )
        db_session.add(school)
        db_session.commit()

        result = import_data(
            db=db_session,
            entity_type="students",
            file_content=b"first_name,last_name,gender\n",
            filename="empty.csv",
            school_id=school.id,
        )
        assert result.inserted_rows == 0
        assert len(result.errors) >= 1
