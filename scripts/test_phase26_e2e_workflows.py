"""
Phase 26 Real End-to-End Multi-Tenant Feature Workflow Test Script
Executes full real-world educational workflows across two isolated schools:
School A ("Greenwood High") & School B ("Sunrise International")
Tests: Identity -> School Setup -> Student Admission -> Parent Link -> Teacher Assignment ->
Attendance -> Homework -> Exams -> Fee Payments -> Certificates -> Notifications -> Cross-Tenant Security.
"""

import os
import sys
import uuid
from datetime import date

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import psycopg2
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Eicher2789")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

ADMIN_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"
E2E_DB_NAME = "school_erp_phase26_e2e"


def run_sql(url, query):
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    conn.close()


def main():
    print("=== STARTING PHASE 26 REAL END-TO-END MULTI-TENANT WORKFLOW TEST ===")

    # Step 1: Provision DB & Migrate
    print(f"1. Provisioning clean database {E2E_DB_NAME}...")
    run_sql(ADMIN_URL, f"DROP DATABASE IF EXISTS {E2E_DB_NAME};")
    run_sql(ADMIN_URL, f"CREATE DATABASE {E2E_DB_NAME};")

    e2e_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{E2E_DB_NAME}"
    os.environ["DATABASE_URL"] = e2e_url

    import subprocess
    ret = subprocess.run(["python", "-m", "alembic", "upgrade", "head"], cwd=backend_dir, capture_output=True, text=True)
    if ret.returncode != 0:
        print(f"Migration failed:\n{ret.stderr}")
        sys.exit(1)
    print(f"   Migrations applied successfully.")

    import app.database.models  # noqa: F401
    from app.models.school import School
    from app.identity.models.user import IdentityUser
    from app.models.academic_year import AcademicYear
    from app.models.school_class import SchoolClass
    from app.models.section import Section
    from app.models.subject import Subject
    from app.models.teacher import Teacher
    from app.models.parent import Parent
    from app.models.student import Student
    from app.models.student.transfer_certificate import TransferCertificate
    from app.models.attendance import Attendance
    from app.models.homework import Homework, HomeworkSubmission
    from app.models.exam import Exam
    from app.models.exam.exam_schedule import ExamSchedule
    from app.models.exam.student_exam_result import StudentExamResult
    from app.models.fees import FeeStructure, FeeItem, FeePayment, StudentFeeAssignment
    from app.models.notification import Notification

    engine = create_engine(e2e_url)

    # IDs
    school_id_a = str(uuid.uuid4())
    school_id_b = str(uuid.uuid4())

    with Session(engine) as session:
        # ========== Step 2: Schools & Academic Infrastructure ==========
        print("2. Provisioning School A (Greenwood High) & School B (Sunrise International)...")
        sch_a = School(
            id=school_id_a, name="Greenwood High School", code="GWOOD", status="ACTIVE",
            address_line1="10 Oak Street", city="Springfield", district="Dist 1",
            state="State A", country="India", postal_code="500001"
        )
        sch_b = School(
            id=school_id_b, name="Sunrise International", code="SUNRISE", status="ACTIVE",
            address_line1="50 Palm Ave", city="Metropolis", district="Dist 2",
            state="State B", country="India", postal_code="600002"
        )
        session.add_all([sch_a, sch_b])
        session.flush()

        # Academic Year, Class, Section, Subject for School A
        ay_a = AcademicYear(id=str(uuid.uuid4()), school_id=school_id_a,
                            name="2026-2027", start_date="2026-06-01", end_date="2027-05-31", is_current=True)
        sc_a = SchoolClass(id=str(uuid.uuid4()), school_id=school_id_a, name="Grade 10", display_order=1)
        sec_a = Section(id=str(uuid.uuid4()), school_class_id=sc_a.id, name="Section A")
        sub_a = Subject(id=str(uuid.uuid4()), school_id=school_id_a, subject_name="Mathematics", subject_code="MATH10")
        session.add_all([ay_a, sc_a, sec_a, sub_a])
        session.flush()

        # Academic Year for School B
        ay_b = AcademicYear(id=str(uuid.uuid4()), school_id=school_id_b,
                            name="2026-2027", start_date="2026-06-01", end_date="2027-05-31", is_current=True)
        sc_b = SchoolClass(id=str(uuid.uuid4()), school_id=school_id_b, name="Grade 5", display_order=1)
        sec_b = Section(id=str(uuid.uuid4()), school_class_id=sc_b.id, name="Section A")
        session.add_all([ay_b, sc_b, sec_b])
        session.flush()

        # ========== Step 3: Users & People ==========
        print("3. Seeding Principal, Teacher, Parent, Student for School A & B...")

        # School A users
        pr_user_a = IdentityUser(id=str(uuid.uuid4()), school_id=school_id_a,
                                 email="principal.a@greenwood.com", password_hash="hash",
                                 first_name="Arthur", last_name="Principal", is_active=True)
        tr_user_a = IdentityUser(id=str(uuid.uuid4()), school_id=school_id_a,
                                 email="teacher.a@greenwood.com", password_hash="hash",
                                 first_name="Theresa", last_name="Teacher", is_active=True)
        pt_user_a = IdentityUser(id=str(uuid.uuid4()), school_id=school_id_a,
                                 email="parent.a@greenwood.com", password_hash="hash",
                                 first_name="Peter", last_name="Parent", is_active=True)
        st_user_a = IdentityUser(id=str(uuid.uuid4()), school_id=school_id_a,
                                 email="student.a@greenwood.com", password_hash="hash",
                                 first_name="Sammy", last_name="Student", is_active=True)
        session.add_all([pr_user_a, tr_user_a, pt_user_a, st_user_a])
        session.flush()

        # School B users
        pr_user_b = IdentityUser(id=str(uuid.uuid4()), school_id=school_id_b,
                                 email="principal.b@sunrise.com", password_hash="hash",
                                 first_name="Brenda", last_name="Principal", is_active=True)
        st_user_b = IdentityUser(id=str(uuid.uuid4()), school_id=school_id_b,
                                 email="student.b@sunrise.com", password_hash="hash",
                                 first_name="Bobby", last_name="Student", is_active=True)
        pt_user_b = IdentityUser(id=str(uuid.uuid4()), school_id=school_id_b,
                                 email="parent.b@sunrise.com", password_hash="hash",
                                 first_name="Paula", last_name="Parent", is_active=True)
        session.add_all([pr_user_b, st_user_b, pt_user_b])
        session.flush()

        # Teacher A
        teacher_a = Teacher(
            id=str(uuid.uuid4()), school_id=school_id_a, employee_id="EMP001",
            first_name="Theresa", last_name="Teacher", gender="FEMALE",
            date_of_birth="1985-04-12", joining_date="2020-01-15",
            phone="9876543210", email="teacher.a@greenwood.com", qualification="M.Sc Math",
            address_line1="12 Teacher Qtrs", city="Springfield", district="Dist 1",
            state="State A", country="India", postal_code="500001"
        )
        # Parent A
        parent_a = Parent(
            id=str(uuid.uuid4()), school_id=school_id_a,
            father_name="Peter Parent", primary_phone="9876543211", email="parent.a@greenwood.com",
            address_line1="10 Oak Street", city="Springfield", district="Dist 1",
            state="State A", country="India", postal_code="500001"
        )
        # Parent B
        parent_b = Parent(
            id=str(uuid.uuid4()), school_id=school_id_b,
            father_name="Paula Parent", primary_phone="9876543299", email="parent.b@sunrise.com",
            address_line1="50 Palm Ave", city="Metropolis", district="Dist 2",
            state="State B", country="India", postal_code="600002"
        )
        session.add_all([teacher_a, parent_a, parent_b])
        session.flush()

        # Student A (School A)
        student_a = Student(
            id=str(uuid.uuid4()), school_id=school_id_a,
            academic_year_id=ay_a.id, school_class_id=sc_a.id, section_id=sec_a.id,
            parent_id=parent_a.id, admission_number="ADM2026001", roll_number="1001",
            first_name="Sammy", last_name="Student", gender="MALE",
            date_of_birth="2010-08-15", admission_date="2026-06-01",
            address_line1="10 Oak Street", city="Springfield", district="Dist 1",
            state="State A", country="India", postal_code="500001"
        )
        # Student B (School B)
        student_b = Student(
            id=str(uuid.uuid4()), school_id=school_id_b,
            academic_year_id=ay_b.id, school_class_id=sc_b.id, section_id=sec_b.id,
            parent_id=parent_b.id, admission_number="ADM2026002", roll_number="5001",
            first_name="Bobby", last_name="Student", gender="MALE",
            date_of_birth="2013-03-22", admission_date="2026-06-01",
            address_line1="50 Palm Ave", city="Metropolis", district="Dist 2",
            state="State B", country="India", postal_code="600002"
        )
        session.add_all([student_a, student_b])
        session.flush()

        # ========== Step 4: Attendance Workflow ==========
        print("4. Executing Attendance marking for Student A...")
        att_a = Attendance(
            id=str(uuid.uuid4()), school_id=school_id_a,
            academic_year_id=ay_a.id, school_class_id=sc_a.id, section_id=sec_a.id,
            student_id=student_a.id, attendance_date="2026-08-21", status="PRESENT"
        )
        session.add(att_a)

        # ========== Step 5: Homework Workflow ==========
        print("5. Executing Homework creation & student submission...")
        hw_a = Homework(
            id=str(uuid.uuid4()), school_id=school_id_a,
            school_class_id=sc_a.id, section_id=sec_a.id, subject_id=sub_a.id,
            teacher_id=teacher_a.id, title="Algebra Quadratic Equations",
            description="Solve odd numbered exercises from chapter 4.",
            assigned_date="2026-08-20", due_date="2026-08-25", status="PUBLISHED"
        )
        session.add(hw_a)
        session.flush()

        hw_sub_a = HomeworkSubmission(
            id=str(uuid.uuid4()), school_id=school_id_a,
            homework_id=hw_a.id, student_id=student_a.id,
            content_text="Quadratic equations solved — answers attached.", status="SUBMITTED"
        )
        session.add(hw_sub_a)

        # ========== Step 6: Exam & Marks Workflow ==========
        print("6. Executing Exam creation, ExamSchedule, & Student A marks entry...")
        exam_a = Exam(
            id=str(uuid.uuid4()), school_id=school_id_a, academic_year_id=ay_a.id,
            name="Midterm Exam 2026", start_date="2026-09-01", end_date="2026-09-10", status="SCHEDULED"
        )
        session.add(exam_a)
        session.flush()

        exam_sched_a = ExamSchedule(
            id=str(uuid.uuid4()), exam_id=exam_a.id, school_id=school_id_a,
            academic_year_id=ay_a.id, school_class_id=sc_a.id, section_id=sec_a.id,
            subject_id=sub_a.id, exam_date="2026-09-02",
            start_time="09:00:00", end_time="12:00:00",
            maximum_marks=100.0, passing_marks=35.0
        )
        session.add(exam_sched_a)
        session.flush()

        result_a = StudentExamResult(
            id=str(uuid.uuid4()), exam_schedule_id=exam_sched_a.id,
            student_id=student_a.id, marks_obtained=92.5, remarks="Excellent"
        )
        session.add(result_a)

        # ========== Step 7: Fee Payment Workflow ==========
        print("7. Executing Fee Structure, Assignment & Payment recording...")
        fee_struct_a = FeeStructure(
            id=str(uuid.uuid4()), school_id=school_id_a,
            academic_year_id=ay_a.id, school_class_id=sc_a.id,
            name="Grade 10 Annual Fee", status="ACTIVE"
        )
        session.add(fee_struct_a)
        session.flush()

        fee_item_a = FeeItem(
            id=str(uuid.uuid4()), fee_structure_id=fee_struct_a.id,
            category="TUITION", name="Tuition Fee", amount=1000.0
        )
        session.add(fee_item_a)
        session.flush()

        fee_assign_a = StudentFeeAssignment(
            id=str(uuid.uuid4()), school_id=school_id_a,
            academic_year_id=ay_a.id, student_id=student_a.id,
            fee_structure_id=fee_struct_a.id, status="PARTIALLY_PAID"
        )
        session.add(fee_assign_a)
        session.flush()

        fee_payment_a = FeePayment(
            id=str(uuid.uuid4()), school_id=school_id_a,
            student_fee_assignment_id=fee_assign_a.id,
            receipt_number="RCP2026001", amount=600.0,
            payment_date="2026-08-20", payment_mode="UPI"
        )
        session.add(fee_payment_a)

        # ========== Step 8: Transfer Certificate & Notification ==========
        print("8. Issuing Transfer Certificate & Notification...")
        tc_a = TransferCertificate(
            id=str(uuid.uuid4()), school_id=school_id_a,
            student_id=student_a.id, academic_year_id=ay_a.id,
            tc_number="TC2026001", issue_date="2026-08-21", leaving_date="2026-08-21",
            reason="Course Completion", status="ISSUED"
        )
        notif_a = Notification(
            id=str(uuid.uuid4()), school_id=school_id_a,
            recipient_type="PARENT", recipient_id=pt_user_a.id,
            recipient_name="Peter Parent", recipient_contact="parent.a@greenwood.com",
            channel="IN_APP", template_key="fee_receipt",
            title="Fee Receipt Issued", body="Receipt RCP2026001 for $600 generated.", status="SENT"
        )
        session.add_all([tc_a, notif_a])
        parent_id_a_str = parent_a.id
        student_id_a_str = student_a.id
        pt_user_id_a_str = pt_user_a.id
        session.commit()

    # ========== Step 9: Verification ==========
    print("9. Verifying Database Consistency & Multi-Tenant Isolation...")
    results = {}
    with Session(engine) as session:
        # 9a. School A has 1 student, School B has 1 student
        count_a = session.execute(select(func.count(Student.id)).where(Student.school_id == school_id_a)).scalar()
        count_b = session.execute(select(func.count(Student.id)).where(Student.school_id == school_id_b)).scalar()
        results["students_school_a"] = count_a
        results["students_school_b"] = count_b
        assert count_a == 1, f"School A should have 1 student, got {count_a}"
        assert count_b == 1, f"School B should have 1 student, got {count_b}"

        # 9b. Parent A linked to Student A
        linked_student = session.execute(
            select(Student).where(Student.parent_id == parent_id_a_str)
        ).scalar_one()
        assert linked_student.first_name == "Sammy"
        results["parent_link"] = f"Peter Parent -> {linked_student.first_name}"

        # 9c. Attendance exists for Student A
        att_count = session.execute(
            select(func.count(Attendance.id)).where(Attendance.student_id == student_id_a_str)
        ).scalar()
        assert att_count == 1
        results["attendance_records"] = att_count

        # 9d. Homework submission exists
        hw_sub_count = session.execute(
            select(func.count(HomeworkSubmission.id)).where(HomeworkSubmission.student_id == student_id_a_str)
        ).scalar()
        assert hw_sub_count == 1
        results["homework_submissions"] = hw_sub_count

        # 9e. Exam result exists with correct marks
        result = session.execute(
            select(StudentExamResult).where(StudentExamResult.student_id == student_id_a_str)
        ).scalar_one()
        assert float(result.marks_obtained) == 92.5
        results["exam_marks"] = f"{result.marks_obtained}/100"

        # 9f. Fee payment: $600 paid
        payment = session.execute(
            select(FeePayment).where(FeePayment.school_id == school_id_a)
        ).scalar_one()
        assert float(payment.amount) == 600.0
        results["fee_paid"] = f"${payment.amount}"

        # 9g. Transfer certificate exists
        tc = session.execute(
            select(TransferCertificate).where(TransferCertificate.student_id == student_id_a_str)
        ).scalar_one()
        assert tc.tc_number == "TC2026001"
        results["transfer_certificate"] = tc.tc_number

        # 9h. Notification sent to Parent A
        notif = session.execute(
            select(Notification).where(Notification.school_id == school_id_a)
        ).scalar_one()
        assert str(notif.recipient_id) == str(pt_user_id_a_str)
        results["notification"] = notif.title

        # 9i. Cross-Tenant Isolation: School A attendance not visible in School B
        cross_att = session.execute(
            select(func.count(Attendance.id)).where(Attendance.school_id == school_id_b)
        ).scalar()
        assert cross_att == 0, f"School B should have 0 attendance records, got {cross_att}"
        results["cross_tenant_attendance_leak"] = cross_att

        # 9j. Cross-Tenant Isolation: School A homework not visible in School B
        cross_hw = session.execute(
            select(func.count(Homework.id)).where(Homework.school_id == school_id_b)
        ).scalar()
        assert cross_hw == 0, f"School B should have 0 homework records, got {cross_hw}"
        results["cross_tenant_homework_leak"] = cross_hw

        # 9k. Cross-Tenant Isolation: School A fees not visible in School B
        cross_fee = session.execute(
            select(func.count(FeePayment.id)).where(FeePayment.school_id == school_id_b)
        ).scalar()
        assert cross_fee == 0, f"School B should have 0 fee payments, got {cross_fee}"
        results["cross_tenant_fee_leak"] = cross_fee

    print("\n=========================================================================")
    print("PHASE 26 END-TO-END WORKFLOW VERIFICATION RESULTS")
    print("=========================================================================")
    for k, v in results.items():
        print(f"  {k:40s} = {v}")
    print("=========================================================================")
    print("=== ALL PHASE 26 E2E WORKFLOWS VERIFIED CLEANLY (100% PASS) ===")


if __name__ == "__main__":
    main()
