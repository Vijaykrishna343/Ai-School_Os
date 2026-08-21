"""
Database Backup & Restoration End-to-End Test Script
Tests creation of database, migration, seeding representative multi-tenant data,
executing pg_dump backup, restoring to a fresh database, and verifying data integrity & tenant isolation.
"""

import os
import subprocess
import sys
import uuid

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import psycopg2
from sqlalchemy import create_engine, text

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Eicher2789")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

ADMIN_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"
ORIG_DB_NAME = "school_erp_backup_orig"
REST_DB_NAME = "school_erp_backup_rest"
DUMP_FILE = os.path.join(os.path.dirname(__file__), "test_backup.dump")


def run_sql(url, query, fetch=False):
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(query)
    res = None
    if fetch:
        res = cur.fetchall()
    cur.close()
    conn.close()
    return res


def main():
    print("=== STARTING BACKUP & RESTORE TEST ===")

    # Step 1: Create original test database
    print(f"1. Creating database {ORIG_DB_NAME}...")
    run_sql(ADMIN_URL, f"DROP DATABASE IF EXISTS {ORIG_DB_NAME};")
    run_sql(ADMIN_URL, f"CREATE DATABASE {ORIG_DB_NAME};")

    orig_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{ORIG_DB_NAME}"

    # Step 2: Apply Alembic Migrations
    print(f"2. Running alembic upgrade head on {ORIG_DB_NAME}...")
    env = os.environ.copy()
    env["DATABASE_URL"] = orig_url
    ret = subprocess.run(["python", "-m", "alembic", "upgrade", "head"], cwd=os.path.join(os.path.dirname(__file__), "..", "backend"), env=env, capture_output=True, text=True)
    if ret.returncode != 0:
        print(f"Migration failed:\n{ret.stderr}")
        sys.exit(1)

    # Step 3: Insert representative multi-tenant data
    print(f"3. Inserting representative multi-tenant data into {ORIG_DB_NAME}...")
    engine = create_engine(orig_url)
    import app.database.models  # noqa: F401 - Register all SQLAlchemy models with Base
    from app.models.school import School
    from app.identity.models.user import IdentityUser
    from sqlalchemy.orm import Session

    school_id_a = str(uuid.uuid4())
    school_id_b = str(uuid.uuid4())

    with Session(engine) as session:
        sch_a = School(
            id=school_id_a,
            name="Alpha Academy",
            code="ALPHA",
            status="ACTIVE",
            address_line1="123 Main St",
            city="Cityville",
            district="District 1",
            state="State 1",
            country="India",
            postal_code="123456",
        )
        sch_b = School(
            id=school_id_b,
            name="Beta Institute",
            code="BETA",
            status="ACTIVE",
            address_line1="456 High St",
            city="Metropolis",
            district="District 2",
            state="State 2",
            country="India",
            postal_code="654321",
        )
        session.add_all([sch_a, sch_b])
        session.flush()

        usr_a = IdentityUser(
            id=str(uuid.uuid4()),
            school_id=school_id_a,
            email="admin@alpha.com",
            password_hash="hash",
            first_name="Alpha",
            last_name="Admin",
            is_active=True,
        )
        usr_b = IdentityUser(
            id=str(uuid.uuid4()),
            school_id=school_id_b,
            email="admin@beta.com",
            password_hash="hash",
            first_name="Beta",
            last_name="Admin",
            is_active=True,
        )
        session.add_all([usr_a, usr_b])
        session.commit()

    print("Data seeded successfully.")

    # Step 4: Perform pg_dump
    print(f"4. Executing pg_dump to {DUMP_FILE}...")
    if os.path.exists(DUMP_FILE):
        os.remove(DUMP_FILE)

    pg_dump_bin = "pg_dump"
    pg_restore_bin = "pg_restore"
    win_pg_bin = r"C:\Program Files\PostgreSQL\16\bin"
    if os.path.exists(os.path.join(win_pg_bin, "pg_dump.exe")):
        pg_dump_bin = os.path.join(win_pg_bin, "pg_dump.exe")
        pg_restore_bin = os.path.join(win_pg_bin, "pg_restore.exe")

    pg_env = os.environ.copy()
    pg_env["PGPASSWORD"] = DB_PASS
    dump_cmd = [pg_dump_bin, "-h", DB_HOST, "-U", DB_USER, "-d", ORIG_DB_NAME, "-F", "c", "-f", DUMP_FILE]
    ret = subprocess.run(dump_cmd, env=pg_env, capture_output=True, text=True)
    if ret.returncode != 0:
        print(f"pg_dump failed:\n{ret.stderr}")
        sys.exit(1)
    print("Backup created successfully.")

    # Step 5: Create restored database & restore
    print(f"5. Creating database {REST_DB_NAME} and performing pg_restore...")
    run_sql(ADMIN_URL, f"DROP DATABASE IF EXISTS {REST_DB_NAME};")
    run_sql(ADMIN_URL, f"CREATE DATABASE {REST_DB_NAME};")

    restore_cmd = [pg_restore_bin, "-h", DB_HOST, "-U", DB_USER, "-d", REST_DB_NAME, "-v", DUMP_FILE]
    subprocess.run(restore_cmd, env=pg_env, capture_output=True, text=True)

    # Step 6: Verify restored data integrity & tenant isolation
    print(f"6. Verifying data integrity & tenant isolation in {REST_DB_NAME}...")
    rest_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{REST_DB_NAME}"
    rest_engine = create_engine(rest_url)

    with rest_engine.connect() as conn:
        schools = conn.execute(text("SELECT id, name FROM schools ORDER BY name")).fetchall()
        print(f"Restored Schools: {schools}")
        assert len(schools) == 2, f"Expected 2 schools, got {len(schools)}"

        users_a = conn.execute(text("SELECT email FROM identity_users WHERE school_id = :sid"), {"sid": school_id_a}).fetchall()
        users_b = conn.execute(text("SELECT email FROM identity_users WHERE school_id = :sid"), {"sid": school_id_b}).fetchall()

        assert len(users_a) == 1 and users_a[0][0] == "admin@alpha.com"
        assert len(users_b) == 1 and users_b[0][0] == "admin@beta.com"

        print("Tenant isolation & data integrity verified cleanly!")

    # Cleanup
    if os.path.exists(DUMP_FILE):
        os.remove(DUMP_FILE)

    print("=== BACKUP & RESTORE TEST PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()