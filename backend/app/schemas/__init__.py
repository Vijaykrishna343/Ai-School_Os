from app.schemas.school import *
from app.schemas.parent import *

from .academic_year import (
    AcademicYearBase,
    AcademicYearCreate,
    AcademicYearResponse,
    AcademicYearUpdate,
)

from .attendance import (
    AttendanceBulkCreate,
    AttendanceBulkItem,
    AttendanceCreate,
    AttendanceListResponse,
    AttendanceResponse,
    AttendanceUpdate,
)

from .school_class import (
    SchoolClassCreate,
    SchoolClassResponse,
    SchoolClassUpdate,
)

from .section import (
    SectionBase,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)

__all__ = [
    "AcademicYearBase",
    "AcademicYearCreate",
    "AcademicYearResponse",
    "AcademicYearUpdate",
    "AttendanceBulkCreate",
    "AttendanceBulkItem",
    "AttendanceCreate",
    "AttendanceListResponse",
    "AttendanceResponse",
    "AttendanceUpdate",
    "SchoolClassCreate",
    "SchoolClassResponse",
    "SchoolClassUpdate",
    "SectionBase",
    "SectionCreate",
    "SectionResponse",
    "SectionUpdate",
]