from .academic_year import AcademicYearStatus
from .school_class import SchoolClassStatus
from .section import SectionStatus
from .subject import SubjectStatus
from .student import (
    AdmissionType,
    StudentStatus,
)
from .teacher import (
    BloodGroup,
    Gender,
    TeacherStatus,
)

__all__ = [
    "AcademicYearStatus",
    "AdmissionType",
    "BloodGroup",
    "Gender",
    "SchoolClassStatus",
    "SectionStatus",
    "StudentStatus",
    "SubjectStatus",
    "TeacherStatus",
]