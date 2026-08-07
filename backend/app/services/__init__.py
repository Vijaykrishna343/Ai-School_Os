from .academic_year_service import (
    AcademicYearService,
    academic_year_service,
)
from .base_service import BaseService
from .parent_service import (
    ParentService,
    parent_service,
)
from .school_class_service import (
    SchoolClassService,
    school_class_service,
)
from .school_service import (
    SchoolService,
    school_service,
)
from .section_service import (
    SectionService,
    section_service,
)
from .student.student_service import (
    StudentService,
    student_service,
)
from .subject.subject_service import (
    SubjectService,
    subject_service,
)
from .teacher.teacher_service import (
    TeacherService,
    teacher_service,
)

__all__ = [
    # Base
    "BaseService",
    # Service classes
    "AcademicYearService",
    "ParentService",
    "SchoolService",
    "SchoolClassService",
    "SectionService",
    "StudentService",
    "SubjectService",
    "TeacherService",
    # Singleton instances
    "academic_year_service",
    "parent_service",
    "school_service",
    "school_class_service",
    "section_service",
    "student_service",
    "subject_service",
    "teacher_service",
]