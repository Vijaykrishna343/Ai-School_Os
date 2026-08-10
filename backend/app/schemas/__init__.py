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

from .fees import (
    FeeDiscountCreate,
    FeeDiscountResponse,
    FeeItemCreate,
    FeeItemResponse,
    FeePaymentCreate,
    FeePaymentListResponse,
    FeePaymentResponse,
    FeeReceiptResponse,
    FeeStructureCreate,
    FeeStructureListResponse,
    FeeStructureResponse,
    FeeStructureUpdate,
    StudentFeeAssignmentCreate,
    StudentFeeAssignmentListResponse,
    StudentFeeAssignmentResponse,
    StudentFeeItemCreate,
    StudentFeeItemResponse,
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
    "FeeDiscountCreate",
    "FeeDiscountResponse",
    "FeeItemCreate",
    "FeeItemResponse",
    "FeePaymentCreate",
    "FeePaymentListResponse",
    "FeePaymentResponse",
    "FeeReceiptResponse",
    "FeeStructureCreate",
    "FeeStructureListResponse",
    "FeeStructureResponse",
    "FeeStructureUpdate",
    "SchoolClassCreate",
    "SchoolClassResponse",
    "SchoolClassUpdate",
    "SectionBase",
    "SectionCreate",
    "SectionResponse",
    "SectionUpdate",
    "StudentFeeAssignmentCreate",
    "StudentFeeAssignmentListResponse",
    "StudentFeeAssignmentResponse",
    "StudentFeeItemCreate",
    "StudentFeeItemResponse",
]