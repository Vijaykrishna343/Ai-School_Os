from app.services.student.student_service import (
    StudentService,
    student_service,
)


def get_student_service() -> StudentService:
    """
    FastAPI dependency that returns the StudentService singleton.
    """
    return student_service