from app.services.teacher.teacher_service import (
    TeacherService,
    teacher_service,
)


def get_teacher_service() -> TeacherService:
    """
    Dependency to provide TeacherService.
    """

    return teacher_service