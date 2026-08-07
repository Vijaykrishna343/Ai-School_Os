from .academic_year.academic_year_repository import (
    AcademicYearRepository,
    academic_year_repository,
)
from .base import BaseRepository
from .parent.parent_repository import (
    ParentRepository,
    parent_repository,
)
from .school.school_repository import (
    SchoolRepository,
    school_repository,
)
from .school_class.school_class_repository import (
    SchoolClassRepository,
    school_class_repository,
)
from .section.section_repository import (
    SectionRepository,
    section_repository,
)
from .student.student_repository import (
    StudentRepository,
    student_repository,
)
from .subject.subject_repository import (
    SubjectRepository,
    subject_repository,
)
from .teacher.teacher_repository import (
    TeacherRepository,
    teacher_repository,
)

__all__ = [
    # Base
    "BaseRepository",
    # Repository classes
    "AcademicYearRepository",
    "ParentRepository",
    "SchoolRepository",
    "SchoolClassRepository",
    "SectionRepository",
    "StudentRepository",
    "SubjectRepository",
    "TeacherRepository",
    # Singleton instances
    "academic_year_repository",
    "parent_repository",
    "school_repository",
    "school_class_repository",
    "section_repository",
    "student_repository",
    "subject_repository",
    "teacher_repository",
]