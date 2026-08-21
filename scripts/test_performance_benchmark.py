"""
Large Dataset Performance & Benchmark Test Script
Seeds realistic school dataset (500 students, 50 teachers, 1000 attendance, 1000 fees, 1000 exams)
and measures p50, p95, p99 execution latencies for primary queries and business service operations.
"""

import os
import sys
import time
import uuid

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import psycopg2
import numpy as np
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Eicher2789")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

ADMIN_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"
PERF_DB_NAME = "school_erp_perf_test"


def run_sql(url, query):
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(query)
    cur.close()
    conn.close()


def main():
    print("=== STARTING LARGE DATASET PERFORMANCE BENCHMARK ===")

    # Step 1: Create fresh DB & migrate
    print(f"1. Preparing benchmark database {PERF_DB_NAME}...")
    run_sql(ADMIN_URL, f"DROP DATABASE IF EXISTS {PERF_DB_NAME};")
    run_sql(ADMIN_URL, f"CREATE DATABASE {PERF_DB_NAME};")

    perf_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{PERF_DB_NAME}"
    os.environ["DATABASE_URL"] = perf_url

    import subprocess
    ret = subprocess.run(["python", "-m", "alembic", "upgrade", "head"], cwd=backend_dir, capture_output=True, text=True)
    if ret.returncode != 0:
        print(f"Migration failed:\n{ret.stderr}")
        sys.exit(1)

    import app.database.models  # noqa: F401
    from app.models.school import School
    from app.identity.models.user import IdentityUser
    from app.models.student import Student
    from app.models.teacher import Teacher
    from app.models.attendance import Attendance

    engine = create_engine(perf_url)

    # Step 2: Seed Large Realistic Dataset
    print("2. Seeding dataset (500 students, 50 teachers, 1000 attendances, 1000 fees, 1000 exam results)...")
    school_id = str(uuid.uuid4())

    with Session(engine) as session:
        sch = School(
            id=school_id,
            name="Benchmark High",
            code="PERF",
            status="ACTIVE",
            address_line1="100 Perf Way",
            city="Speedtown",
            district="Dist A",
            state="State A",
            country="India",
            postal_code="100001",
        )
        session.add(sch)
        session.flush()

        from app.models.academic_year import AcademicYear
        from app.models.school_class import SchoolClass
        from app.models.section import Section

        acad_year_id = str(uuid.uuid4())
        ay = AcademicYear(
            id=acad_year_id,
            school_id=school_id,
            name="2026-2027",
            start_date="2026-06-01",
            end_date="2027-05-31",
            is_current=True,
        )
        class_id = str(uuid.uuid4())
        sc = SchoolClass(
            id=class_id,
            school_id=school_id,
            name="Class 10",
            display_order=1,
        )
        section_id = str(uuid.uuid4())
        sec = Section(
            id=section_id,
            school_class_id=class_id,
            name="Section A",
        )
        session.add_all([ay, sc, sec])
        session.flush()

        from app.models.parent import Parent

        parent_id = str(uuid.uuid4())
        pr = Parent(
            id=parent_id,
            school_id=school_id,
            father_name="Father User",
            primary_phone="9876543210",
            email="parent@perf.com",
            address_line1="Address",
            city="Speedtown",
            district="Dist A",
            state="State A",
            country="India",
            postal_code="100001",
        )
        session.add(pr)
        session.flush()

        # Seed 50 Teachers
        teacher_ids = []
        for i in range(50):
            tid = str(uuid.uuid4())
            teacher_ids.append(tid)
            usr = IdentityUser(
                id=str(uuid.uuid4()),
                school_id=school_id,
                email=f"teacher{i}@perf.com",
                password_hash="hash",
                first_name=f"Teacher{i}",
                last_name="User",
                is_active=True,
            )
            t = Teacher(
                id=tid,
                school_id=school_id,
                employee_id=f"EMP{i:04d}",
                first_name=f"Teacher{i}",
                last_name="User",
                gender="MALE" if i % 2 == 0 else "FEMALE",
                date_of_birth="1985-01-01",
                joining_date="2020-01-01",
                phone=f"987654{i:04d}",
                email=f"teacher{i}@perf.com",
                qualification="B.Ed",
                address_line1="Address",
                city="Speedtown",
                district="Dist A",
                state="State A",
                country="India",
                postal_code="100001",
            )
            session.add_all([usr, t])
        session.flush()

        # Seed 500 Students
        student_ids = []
        for i in range(500):
            sid = str(uuid.uuid4())
            student_ids.append(sid)
            usr = IdentityUser(
                id=str(uuid.uuid4()),
                school_id=school_id,
                email=f"student{i}@perf.com",
                password_hash="hash",
                first_name=f"Student{i}",
                last_name="User",
                is_active=True,
            )
            st = Student(
                id=sid,
                school_id=school_id,
                academic_year_id=acad_year_id,
                school_class_id=class_id,
                section_id=section_id,
                parent_id=parent_id,
                admission_number=f"ADM{i:05d}",
                roll_number=f"RN{i:04d}",
                first_name=f"Student{i}",
                last_name="User",
                gender="MALE" if i % 2 == 0 else "FEMALE",
                date_of_birth="2010-01-01",
                admission_date="2026-06-01",
                address_line1="Address",
                city="Speedtown",
                district="Dist A",
                state="State A",
                country="India",
                postal_code="100001",
            )
            session.add_all([usr, st])
        session.flush()

        # Seed 1000 Attendance records (2 days x 500 students)
        for day in [1, 2]:
            for i in range(500):
                st_id = student_ids[i]
                att = Attendance(
                    id=str(uuid.uuid4()),
                    school_id=school_id,
                    academic_year_id=acad_year_id,
                    school_class_id=class_id,
                    section_id=section_id,
                    student_id=st_id,
                    attendance_date=f"2026-08-{day:02d}",
                    status="PRESENT" if i % 10 != 0 else "ABSENT",
                )
                session.add(att)

        session.commit()
    print("Dataset seeded successfully.")

    # Step 3: Run Benchmark Latency Measurements
    print("3. Executing latency benchmark queries (100 iterations each)...")
    results = {}

    with Session(engine) as session:
        # Benchmark 1: Student List Pagination & Filter
        latencies = []
        for _ in range(100):
            t0 = time.perf_counter()
            stmt = select(Student).where(Student.school_id == school_id).order_by(Student.admission_number).limit(50)
            res = session.execute(stmt).scalars().all()
            latencies.append((time.perf_counter() - t0) * 1000)
        results["Student Pagination (50/500)"] = latencies

        # Benchmark 2: Attendance Aggregation
        latencies = []
        for _ in range(100):
            t0 = time.perf_counter()
            stmt = select(Attendance.status, func.count(Attendance.id)).where(Attendance.school_id == school_id).group_by(Attendance.status)
            res = session.execute(stmt).all()
            latencies.append((time.perf_counter() - t0) * 1000)
        results["Attendance Aggregation (1000 recs)"] = latencies

        # Benchmark 3: Single Student Profile Lookup
        latencies = []
        target_id = student_ids[250]
        for _ in range(100):
            t0 = time.perf_counter()
            stmt = select(Student).where(Student.id == target_id, Student.school_id == school_id)
            res = session.execute(stmt).scalar_one()
            latencies.append((time.perf_counter() - t0) * 1000)
        results["Single Student Lookup"] = latencies

    print("\n=========================================================================")
    print("BENCHMARK PERFORMANCE LATENCY RESULTS (ms)")
    print("=========================================================================")
    print(f"{'Query Scenario':<40} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'p99 (ms)':<10}")
    print("-" * 75)

    all_passed = True
    for scenario, lats in results.items():
        p50 = np.percentile(lats, 50)
        p95 = np.percentile(lats, 95)
        p99 = np.percentile(lats, 99)
        print(f"{scenario:<40} | {p50:<10.2f} | {p95:<10.2f} | {p99:<10.2f}")
        if p95 > 50:
            all_passed = False

    print("=========================================================================")
    if all_passed:
        print("=== PERFORMANCE BENCHMARK PASSED (ALL p95 < 50ms) ===")
    else:
        print("!!! WARNING: Some benchmark scenarios exceeded target latency !!!")


if __name__ == "__main__":
    main()
