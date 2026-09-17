from .academic_year import AcademicYearStatus
from .school_class import SchoolClassStatus
from .section import SectionStatus
from .subject import SubjectStatus
from .attendance import AttendanceStatus
from .exam import AssessmentType, AttemptType, ExamStatus, parse_legacy_exam_type
from .report_card import (
    CalculationMode,
    ReportCardStatus,
    RetestPolicy,
    RoundingMode,
)
from .timetable import (
    DayOfWeek,
    PeriodType,
    RoomType,
    TimetableStatus,
)
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
from .payment import (
    PaymentProvider,
    PaymentOrderStatus,
    PaymentTransactionStatus,
)
from .visitor import (
    HostType,
    IdProofType,
    ReceptionInquiryStatus,
    VisitorStatus,
)
from .transport import (
    FuelType,
    TransportAllocationStatus,
    TransportAllocationType,
    VehicleStatus,
    VehicleType,
)
from .library import (
    BookCondition,
    BookCopyStatus,
    BookLoanStatus,
    BookReservationStatus,
    LibraryFineReason,
    LibraryFineStatus,
    LibraryMemberStatus,
    LibraryMemberType,
)
from .admissions import (
    AdmissionApplicationStatus,
    AdmissionCycleStatus,
    AdmissionDecisionType,
    ApplicantStatus,
)
from .inventory import (
    AssetAssignmentStatus,
    AssetAssignmentType,
    AssetCondition,
    AssetStatus,
    InventoryItemType,
    InventoryLocationType,
    InventoryStockMovementType,
)

__all__ = [
    "AcademicYearStatus",
    "AdmissionApplicationStatus",
    "AdmissionCycleStatus",
    "AdmissionDecisionType",
    "AdmissionType",
    "ApplicantStatus",
    "AssessmentType",
    "AssetAssignmentStatus",
    "AssetAssignmentType",
    "AssetCondition",
    "AssetStatus",
    "AttemptType",
    "AttendanceStatus",
    "BloodGroup",
    "BookCondition",
    "BookCopyStatus",
    "BookLoanStatus",
    "BookReservationStatus",
    "CalculationMode",
    "DayOfWeek",
    "DiscountType",
    "EnrollmentStatus",
    "ExamStatus",
    "FeeCategory",
    "FeeStructureStatus",
    "FuelType",
    "Gender",
    "HostType",
    "IdProofType",
    "InventoryItemType",
    "InventoryLocationType",
    "InventoryStockMovementType",
    "LibraryFineReason",
    "LibraryFineStatus",
    "LibraryMemberStatus",
    "LibraryMemberType",
    "PaymentMode",
    "PaymentOrderStatus",
    "PaymentProvider",
    "PaymentTransactionStatus",
    "PromotionDecision",
    "PeriodType",
    "ReceptionInquiryStatus",
    "ReportCardStatus",
    "RetestPolicy",
    "RoomType",
    "RoundingMode",
    "SchoolClassStatus",
    "SectionStatus",
    "StudentFeeAssignmentStatus",
    "StudentStatus",
    "SubjectStatus",
    "TeacherStatus",
    "TimetableStatus",
    "TransferCertificateStatus",
    "TransportAllocationStatus",
    "TransportAllocationType",
    "VehicleStatus",
    "VehicleType",
    "VisitorStatus",
    "parse_legacy_exam_type",
]

