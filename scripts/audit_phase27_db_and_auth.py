"""
Phase 27 Deep DB & Auth Inspection Script
Inspects database seed users, roles, permissions, schools, and tests authenticating as each role.
"""

import os
import sys
import json
import urllib.request
import urllib.error

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Eicher2789")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "school_erp")

db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

import app.database.models  # noqa: F401
from app.models.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole

BASE_URL = "http://127.0.0.1:8000"

def make_post(path, data):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            body_json = json.loads(content)
        except Exception:
            body_json = {"raw": content}
        return e.code, body_json
    except Exception as e:
        return 0, {"error": str(e)}

def audit_db():
    print("=== AUDITING ACTIVE DATABASE USERS & SCHOOLS ===")
    engine = create_engine(db_url)
    
    with Session(engine) as session:
        schools = session.execute(select(School)).scalars().all()
        print(f"Schools count: {len(schools)}")
        for s in schools:
            print(f"  - School: ID={s.id}, Name={s.name}, Code={s.code}, Status={s.status}")

        users = session.execute(select(IdentityUser)).scalars().all()
        print(f"\nUsers count: {len(users)}")
        for u in users:
            print(f"  - User: ID={u.id}, Email={u.email}, SchoolID={u.school_id}, Active={u.is_active}")

        roles = session.execute(select(IdentityRole)).scalars().all()
        print(f"\nRoles count: {len(roles)}")
        for r in roles:
            print(f"  - Role: ID={r.id}, Name={r.name}, SchoolID={r.school_id}")

    print("\n=== PROBING LOGIN FOR SEED USERS ===")
    test_users = [
        ("superadmin@schoolos.com", "SuperAdmin123!"),
        ("principal@vaagdevi.com", "Principal123!"),
        ("teacher@vaagdevi.com", "Teacher123!"),
        ("classteacher@vaagdevi.com", "ClassTeacher123!"),
        ("parent@vaagdevi.com", "Parent123!"),
        ("student@vaagdevi.com", "Student123!"),
    ]
    for email, pwd in test_users:
        status, body = make_post("/api/v1/auth/login", {
            "school_code": "VGS001",
            "email": email,
            "password": pwd
        })
        print(f"  Login {email}: Status={status}, Response={body.get('message') or 'Success' if status == 200 else body}")

if __name__ == "__main__":
    audit_db()
