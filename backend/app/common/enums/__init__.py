from .academic_year import AcademicYearStatus
from .school_class import SchoolClassStatus
from .section import SectionStatus
from .subject import SubjectStatus
from .attendance import AttendanceStatus
from .exam import AssessmentType, AttemptType, ExamStatus, parse_legacy_exam_type
from .fees import (
    DiscountType,
    FeeCategory,
    FeeStructureStatus,
    PaymentMode,
    StudentFeeAssignmentStatus,
)
from .student import (
    AdmissionType,
    EnrollmentStatus,
    PromotionDecision,
    StudentStatus,
    TransferCertificateStatus,
)
from .teacher import (
    BloodGroup,
    Gender,
    TeacherStatus,
)

__all__ = [
    "AcademicYearStatus",
    "AdmissionType",
    "AssessmentType",
    "AttemptType",
    "AttendanceStatus",
    "BloodGroup",
    "DiscountType",
    "EnrollmentStatus",
    "ExamStatus",
    "FeeCategory",
    "FeeStructureStatus",
    "Gender",
    "PaymentMode",
    "PromotionDecision",
    "SchoolClassStatus",
    "SectionStatus",
    "StudentFeeAssignmentStatus",
    "StudentStatus",
    "SubjectStatus",
    "TeacherStatus",
    "TransferCertificateStatus",
    "parse_legacy_exam_type",
]
