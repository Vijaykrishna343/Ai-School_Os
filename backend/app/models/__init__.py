from .academic_year import (
    AcademicYear,
    ClassProgressionRule,
    ProgressionExecution,
    ProgressionExecutionItem,
    ProgressionExecutionStatus,
)
from .attendance import Attendance
from .fees import (
    FeeDiscount,
    FeeItem,
    FeePayment,
    FeeStructure,
    StudentFeeAssignment,
    StudentFeeItem,
)
from .parent import Parent
from .school import School
from .school_class import SchoolClass
from .section import Section
from .student import (
    Student,
    StudentEnrollmentHistory,
    TransferCertificate,
)
from .subject import Subject
from .teacher import Teacher
from .notification import Notification, NotificationChannel, NotificationStatus, NotificationRecipientType
from .audit_log import AuditLog
from .hostel import (
    HostelBuilding,
    HostelRoom,
    HostelBed,
    HostelAllocation,
    HostelAttendance,
    HostelOutpass,
    HostelFeeStructure,
    HostelFeeAllocation,
)
from .event import SchoolEvent
from .staff_leave import (
    StaffLeaveType,
    StaffLeaveBalance,
    StaffLeaveRequest,
    StaffLeaveApprovalHistory,
)
from .communication import (
    UserCommunicationPreference,
    NotificationTemplate,
    InAppNotificationRead,
)
from .ai import (
    AIProviderConfig,
    AIAuditLog,
    AIUsageLimit,
    AITimetableDraft,
    AITimetableDraftEntry,
    AIStudentRiskAssessment,
    AICommunicationDraft,
    AIReportCardRemark,
)
from .payment import (
    PaymentOrder,
    PaymentTransaction,
)
from .visitor import (
    ReceptionInquiry,
    Visitor,
)
from .transport import (
    Vehicle,
    TransportDriver,
    TransportRoute,
    RouteStop,
    StudentTransportAllocation,
)
from .library import (
    Book,
    BookCategory,
    BookCopy,
    BookLoan,
    BookReservation,
    Library,
    LibraryFine,
    LibraryMember,
)
from .admissions import (
    AdmissionApplication,
    AdmissionCycle,
    AdmissionDecision,
    Applicant,
    ApplicationStatusHistory,
)
from .inventory import (
    AssetAssignment,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventoryStock,
    InventoryStockMovement,
    InventoryVendor,
    PhysicalAsset,
)

__all__ = [
    "AcademicYear",
    "AdmissionApplication",
    "AdmissionCycle",
    "AdmissionDecision",
    "Applicant",
    "ApplicationStatusHistory",
    "AssetAssignment",
    "AIProviderConfig",
    "AIAuditLog",
    "AIUsageLimit",
    "AIStudentRiskAssessment",
    "AICommunicationDraft",
    "AIReportCardRemark",
    "Attendance",
    "AuditLog",
    "Book",
    "BookCategory",
    "BookCopy",
    "BookLoan",
    "BookReservation",
    "ClassProgressionRule",
    "ProgressionExecution",
    "ProgressionExecutionItem",
    "ProgressionExecutionStatus",
    "FeeDiscount",
    "FeeItem",
    "FeePayment",
    "FeeStructure",
    "HostelBuilding",
    "HostelRoom",
    "HostelBed",
    "HostelAllocation",
    "HostelAttendance",
    "HostelOutpass",
    "HostelFeeStructure",
    "HostelFeeAllocation",
    "InventoryCategory",
    "InventoryItem",
    "InventoryLocation",
    "InventoryStock",
    "InventoryStockMovement",
    "InventoryVendor",
    "Library",
    "LibraryFine",
    "LibraryMember",
    "PaymentOrder",
    "PaymentTransaction",
    "PhysicalAsset",
    "ReceptionInquiry",
    "RouteStop",
    "SchoolEvent",
    "StaffLeaveType",
    "StaffLeaveBalance",
    "StaffLeaveRequest",
    "StaffLeaveApprovalHistory",
    "StudentTransportAllocation",
    "TransportDriver",
    "TransportRoute",
    "UserCommunicationPreference",
    "NotificationTemplate",
    "InAppNotificationRead",
    "Notification",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationRecipientType",
    "Parent",
    "School",
    "SchoolClass",
    "Section",
    "Student",
    "StudentEnrollmentHistory",
    "StudentFeeAssignment",
    "StudentFeeItem",
    "Subject",
    "Teacher",
    "TransferCertificate",
    "Vehicle",
    "Visitor",
]

