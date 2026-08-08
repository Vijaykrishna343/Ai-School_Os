"""
Dependency provider functions for FastAPI.

All functions return singleton service/repository instances.
No service or repository is ever instantiated here.
"""

from app.repositories.academic_year import academic_year_repository
from app.repositories.attendance import attendance_repository
from app.repositories.parent import parent_repository
from app.repositories.school import school_repository
from app.repositories.school_class import school_class_repository
from app.repositories.section import section_repository
from app.repositories.student import student_repository
from app.repositories.subject import subject_repository
from app.repositories.teacher import teacher_repository
from app.services.academic_year_service import (
    AcademicYearService,
    academic_year_service,
)
from app.services.attendance_service import (
    AttendanceService,
    attendance_service,
)
from app.services.parent_service import (
    ParentService,
    parent_service,
)
from app.services.school_class_service import (
    SchoolClassService,
    school_class_service,
)
from app.services.school_service import (
    SchoolService,
    school_service,
)
from app.services.section_service import (
    SectionService,
    section_service,
)
from app.services.student.student_service import (
    StudentService,
    student_service,
)
from app.services.subject.subject_service import (
    SubjectService,
    subject_service,
)
from app.services.teacher.teacher_service import (
    TeacherService,
    teacher_service,
)


# ------------------------------------------------------------------
# Repository Dependencies
# ------------------------------------------------------------------


def get_school_repository():
    """Return the SchoolRepository singleton."""
    return school_repository


def get_parent_repository():
    """Return the ParentRepository singleton."""
    return parent_repository


def get_academic_year_repository():
    """Return the AcademicYearRepository singleton."""
    return academic_year_repository


def get_attendance_repository():
    """Return the AttendanceRepository singleton."""
    return attendance_repository


def get_school_class_repository():
    """Return the SchoolClassRepository singleton."""
    return school_class_repository


def get_section_repository():
    """Return the SectionRepository singleton."""
    return section_repository


def get_student_repository():
    """Return the StudentRepository singleton."""
    return student_repository


def get_subject_repository():
    """Return the SubjectRepository singleton."""
    return subject_repository


def get_teacher_repository():
    """Return the TeacherRepository singleton."""
    return teacher_repository


# ------------------------------------------------------------------
# Service Dependencies
# ------------------------------------------------------------------


def get_school_service() -> SchoolService:
    """Return the SchoolService singleton."""
    return school_service


def get_parent_service() -> ParentService:
    """Return the ParentService singleton."""
    return parent_service


def get_academic_year_service() -> AcademicYearService:
    """Return the AcademicYearService singleton."""
    return academic_year_service


def get_attendance_service() -> AttendanceService:
    """Return the AttendanceService singleton."""
    return attendance_service


def get_school_class_service() -> SchoolClassService:
    """Return the SchoolClassService singleton."""
    return school_class_service


def get_section_service() -> SectionService:
    """Return the SectionService singleton."""
    return section_service


def get_student_service() -> StudentService:
    """Return the StudentService singleton."""
    return student_service


def get_subject_service() -> SubjectService:
    """Return the SubjectService singleton."""
    return subject_service


def get_teacher_service() -> TeacherService:
    """Return the TeacherService singleton."""
    return teacher_service