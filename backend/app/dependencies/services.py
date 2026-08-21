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
from app.repositories.student import (
    student_repository,
    student_enrollment_history_repository,
    transfer_certificate_repository,
)
from app.repositories.subject import subject_repository
from app.repositories.teacher import teacher_repository
from app.services.teacher.teacher_service import (
    TeacherService,
    teacher_service,
)
from app.services.academic_year_service import (
    AcademicYearService,
    academic_year_service,
)
from app.services.class_progression_rule_service import (
    ClassProgressionRuleService,
    class_progression_rule_service,
)
from app.services.student.progression_preview_service import (
    ProgressionPreviewService,
    progression_preview_service,
)
from app.services.student.progression_planner import (
    ProgressionPlanner,
    progression_planner,
)
from app.services.student.progression_execution_service import (
    ProgressionExecutionService,
    progression_execution_service,
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
from app.repositories.academic_term import academic_term_repository
from app.services.academic_term_service import (
    AcademicTermService,
    academic_term_service,
)
from app.repositories.grading import (
    evaluation_config_repository,
    grade_scale_repository,
    report_card_repository,
)
from app.services.evaluation_config_service import (
    EvaluationConfigService,
    evaluation_config_service,
)
from app.services.grading_scale_service import (
    GradeScaleService,
    grade_scale_service,
)
from app.services.report_card_service import (
    ReportCardService,
    report_card_service,
)
from app.repositories.timetable import (
    period_slot_repository,
    classroom_repository,
    timetable_repository,
    timetable_entry_repository,
    teacher_substitution_repository,
)
from app.services.period_slot_service import (
    PeriodSlotService,
    period_slot_service,
)
from app.services.classroom_service import (
    ClassroomService,
    classroom_service,
)
from app.services.timetable_service import (
    TimetableService,
    timetable_service,
)
from app.services.timetable_entry_service import (
    TimetableEntryService,
    timetable_entry_service,
)
from app.services.timetable_conflict_service import (
    TimetableConflictService,
    timetable_conflict_service,
)
from app.services.teacher_substitution_service import (
    TeacherSubstitutionService,
    teacher_substitution_service,
)
from app.services.dashboard_service import (
    DashboardService,
    dashboard_service,
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


def get_academic_term_repository():
    """Return the AcademicTermRepository singleton."""
    return academic_term_repository


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


def get_evaluation_config_repository():
    """Return the EvaluationConfigRepository singleton."""
    return evaluation_config_repository


def get_report_card_repository():
    """Return the ReportCardRepository singleton."""
    return report_card_repository


def get_period_slot_repository():
    """Return the PeriodSlotRepository singleton."""
    return period_slot_repository


def get_classroom_repository():
    """Return the ClassroomRepository singleton."""
    return classroom_repository


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


def get_class_progression_rule_service() -> ClassProgressionRuleService:
    """Return the ClassProgressionRuleService singleton."""
    return class_progression_rule_service


def get_progression_preview_service() -> ProgressionPreviewService:
    """Return the ProgressionPreviewService singleton."""
    return progression_preview_service


def get_progression_planner() -> ProgressionPlanner:
    """Return the ProgressionPlanner singleton."""
    return progression_planner


def get_progression_execution_service() -> ProgressionExecutionService:
    """Return the ProgressionExecutionService singleton."""
    return progression_execution_service


def get_academic_term_service() -> AcademicTermService:
    """Return the AcademicTermService singleton."""
    return academic_term_service


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


def get_grade_scale_repository():
    """Return the GradeScaleRepository singleton."""
    return grade_scale_repository


def get_grade_scale_service() -> GradeScaleService:
    """Return the GradeScaleService singleton."""
    return grade_scale_service


def get_evaluation_config_service() -> EvaluationConfigService:
    """Return the EvaluationConfigService singleton."""
    return evaluation_config_service


def get_report_card_service() -> ReportCardService:
    """Return the ReportCardService singleton."""
    return report_card_service


def get_period_slot_service() -> PeriodSlotService:
    """Return the PeriodSlotService singleton."""
    return period_slot_service


def get_classroom_service() -> ClassroomService:
    """Return the ClassroomService singleton."""
    return classroom_service


def get_timetable_repository():
    """Return the TimetableRepository singleton."""
    return timetable_repository


def get_timetable_entry_repository():
    """Return the TimetableEntryRepository singleton."""
    return timetable_entry_repository


def get_timetable_service() -> TimetableService:
    """Return the TimetableService singleton."""
    return timetable_service


def get_timetable_entry_service() -> TimetableEntryService:
    """Return the TimetableEntryService singleton."""
    return timetable_entry_service


def get_timetable_conflict_service() -> TimetableConflictService:
    """Return the TimetableConflictService singleton."""
    return timetable_conflict_service


def get_teacher_substitution_repository():
    """Return the TeacherSubstitutionRepository singleton."""
    return teacher_substitution_repository


def get_teacher_substitution_service() -> TeacherSubstitutionService:
    """Return the TeacherSubstitutionService singleton."""
    return teacher_substitution_service


def get_dashboard_service() -> DashboardService:
    """Return the DashboardService singleton."""
    return dashboard_service
