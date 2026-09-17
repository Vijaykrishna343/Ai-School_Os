"""
Registers all SQLAlchemy models.

Alembic imports this file so every model is
discovered automatically.
"""

# ==========================
# ERP Models
# ==========================

from app.models.school import School
from app.models.parent import Parent
from app.models.academic_year import (
    AcademicYear,
    ClassProgressionRule,
    ProgressionExecution,
    ProgressionExecutionItem,
)
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.permission import IdentityPermission
from app.identity.models.user_role import IdentityUserRole
from app.identity.models.role_permission import IdentityRolePermission
from app.models.academic_term import AcademicTerm
from app.models.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.student.student_certificate import StudentCertificate, CertificateType
from app.models.teacher.teacher import Teacher
from app.models.teacher.teacher_attendance import TeacherAttendance
from app.models.subject.subject import Subject
from app.models.exam import Exam, ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading import (
    GradeScale,
    GradeScaleEntry,
    EvaluationConfig,
    AssessmentTypeWeightage,
    ReportCard,
    ReportCardItemSnapshot,
)
from app.models.timetable import PeriodSlot, Classroom, Timetable, TimetableEntry, TeacherSubstitution
from app.models.homework import Homework, HomeworkStatus, HomeworkSubmission, SubmissionStatus
from app.models.fees import FeePayment, CashSession
from app.models.payment import PaymentOrder, PaymentTransaction
from app.models.visitor import Visitor, ReceptionInquiry
from app.models.communication import (
    UserCommunicationPreference,
    NotificationTemplate,
    InAppNotificationRead,
    SchoolCommunicationConfig,
    SmsProviderType,
    WhatsAppProviderType,
)
from app.models.notification import Notification
from app.models.transport import (
    Vehicle,
    TransportDriver,
    TransportRoute,
    RouteStop,
    StudentTransportAllocation,
)
from app.models.library import (
    Book,
    BookCategory,
    BookCopy,
    BookLoan,
    BookReservation,
    Library,
    LibraryFine,
    LibraryMember,
)
from app.models.admissions import (
    AdmissionCycle,
    Applicant,
    AdmissionApplication,
    ApplicationStatusHistory,
    AdmissionDecision,
)
from app.models.inventory import (
    InventoryCategory,
    InventoryLocation,
    InventoryVendor,
    InventoryItem,
    InventoryStock,
    PhysicalAsset,
    InventoryStockMovement,
    AssetAssignment,
)

__all__ = [
    "School",
    "Parent",
    "AcademicYear",
    "ClassProgressionRule",
    "ProgressionExecution",
    "ProgressionExecutionItem",
    "AcademicTerm",
    "SchoolClass",
    "Section",
    "Student",
    "Teacher",
    "Subject",
    "Exam",
    "ExamSchedule",
    "IdentityUser",
    "IdentityRole",
    "IdentityPermission",
    "IdentityUserRole",
    "IdentityRolePermission",
    "StudentExamResult",
    "GradeScale",
    "GradeScaleEntry",
    "EvaluationConfig",
    "AssessmentTypeWeightage",
    "ReportCard",
    "ReportCardItemSnapshot",
    "PeriodSlot",
    "Classroom",
    "Timetable",
    "TimetableEntry",
    "TeacherSubstitution",
    "Homework",
    "HomeworkSubmission",
    "Document",
    "FeePayment",
    "CashSession",
    "PaymentOrder",
    "PaymentTransaction",
    "Notification",
    "UserCommunicationPreference",
    "NotificationTemplate",
    "InAppNotificationRead",
    "SchoolCommunicationConfig",
    "SmsProviderType",
    "WhatsAppProviderType",
    "Vehicle",
    "TransportDriver",
    "TransportRoute",
    "RouteStop",
    "StudentTransportAllocation",
    "Book",
    "BookCategory",
    "BookCopy",
    "BookLoan",
    "BookReservation",
    "Library",
    "LibraryFine",
    "LibraryMember",
    "AdmissionCycle",
    "Applicant",
    "AdmissionApplication",
    "ApplicationStatusHistory",
    "AdmissionDecision",
    "InventoryCategory",
    "InventoryLocation",
    "InventoryVendor",
    "InventoryItem",
    "InventoryStock",
    "PhysicalAsset",
    "InventoryStockMovement",
    "AssetAssignment",
]


