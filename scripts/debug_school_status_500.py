import os
import sys
import uuid
import traceback

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Eicher2789")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "school_erp")

db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

import app.database.models  # noqa: F401
from app.services.school_service import school_service
from app.schemas.school.school import SchoolStatusUpdate
from app.common.enums.school import SchoolStatus

engine = create_engine(db_url)
service = school_service

with Session(engine) as db:
    try:
        from app.models.school import School
        from sqlalchemy import select
        sch = db.execute(select(School)).scalars().first()
        print(f"Updating school status for School ID: {sch.id}")
        
        status_update = SchoolStatusUpdate(status=SchoolStatus.SUSPENDED, suspension_reason="Testing suspension")
        res = service.update_school_status(db, sch.id, status_update)
        print("Updated school status successfully:", res.status, res.suspension_reason)
    except Exception:
        traceback.print_exc()
