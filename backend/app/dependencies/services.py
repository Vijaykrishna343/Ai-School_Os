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
from app.services.student.student_promotion_service import (
    StudentPromotionService,
    student_promotion_service,
)
from app.services.student.student_service import (
    StudentService,
    student_service,
)
from app.services.subject.subject_service import (
    SubjectService,
    subject_service,
)
from app.repositories.exam import (
    exam_repository,
    exam_schedule_repository,
    student_exam_result_repository,
)
from app.services.exam_service import (
    ExamService,
    exam_service,
)
from app.services.exam_schedule_service import (
    ExamScheduleService,
    exam_schedule_service,
)
from app.services.student_exam_result_service import (
    StudentExamResultService,
    student_exam_result_service,
)
from app.repositories.fees import (
    fee_payment_repository,
    fee_structure_repository,
    student_fee_assignment_repository,
)
from app.services.fee_service import (
    FeeService,
    fee_service,
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


def get_student_enrollment_history_repository():
    """Return the StudentEnrollmentHistoryRepository singleton."""
    return student_enrollment_history_repository


def get_transfer_certificate_repository():
    """Return the TransferCertificateRepository singleton."""
    return transfer_certificate_repository


def get_subject_repository():
    """Return the SubjectRepository singleton."""
    return subject_repository


def get_teacher_repository():
    """Return the TeacherRepository singleton."""
    return teacher_repository


def get_exam_repository():
    """Return the ExamRepository singleton."""
    return exam_repository


def get_exam_schedule_repository():
    """Return the ExamScheduleRepository singleton."""
    return exam_schedule_repository


def get_student_exam_result_repository():
    """Return the StudentExamResultRepository singleton."""
    return student_exam_result_repository


def get_fee_structure_repository():
    """Return the FeeStructureRepository singleton."""
    return fee_structure_repository


def get_student_fee_assignment_repository():
    """Return the StudentFeeAssignmentRepository singleton."""
    return student_fee_assignment_repository


def get_fee_payment_repository():
    """Return the FeePaymentRepository singleton."""
    return fee_payment_repository


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


def get_student_promotion_service() -> StudentPromotionService:
    """Return the StudentPromotionService singleton."""
    return student_promotion_service


def get_subject_service() -> SubjectService:
    """Return the SubjectService singleton."""
    return subject_service


def get_teacher_service() -> TeacherService:
    """Return the TeacherService singleton."""
    return teacher_service


def get_exam_service() -> ExamService:
    """Return the ExamService singleton."""
    return exam_service


def get_exam_schedule_service() -> ExamScheduleService:
    """Return the ExamScheduleService singleton."""
    return exam_schedule_service


def get_student_exam_result_service() -> StudentExamResultService:
    """Return the StudentExamResultService singleton."""
    return student_exam_result_service


def get_fee_service() -> FeeService:
    """Return the FeeService singleton."""
    return fee_service
