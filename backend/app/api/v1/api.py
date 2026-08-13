from fastapi import APIRouter

from app.api.v1.endpoints.academic_year import (
    router as academic_year_router,
)
from app.api.v1.endpoints.academic_term import (
    router as academic_term_router,
)
from app.api.v1.endpoints.class_progression_rule import (
    router as class_progression_rule_router,
)
from app.api.v1.endpoints.attendance import (
    router as attendance_router,
)
from app.api.v1.endpoints.parent import (
    router as parent_router,
)
from app.api.v1.endpoints.school import (
    router as school_router,
)
from app.api.v1.endpoints.school_class import (
    router as school_class_router,
)
from app.api.v1.endpoints.subject import (
    router as subject_router,
)
from app.api.v1.endpoints.exam import (
    router as exam_router,
)
from app.api.v1.endpoints.exam_schedule import (
    router as exam_schedule_router,
)
from app.api.v1.endpoints.student_exam_result import (
    router as student_exam_result_router,
)
from app.api.v1.endpoints.fees import (
    router as fees_router,
)
from app.api.v1.endpoints.grading_scale import (
    router as grading_scale_router,
)
from app.api.v1.endpoints.evaluation_config import (
    router as evaluation_config_router,
)
from app.api.v1.endpoints.report_card import (
    router as report_card_router,
)
from app.api.v1.endpoints.period_slot import (
    router as period_slot_router,
)
from app.api.v1.endpoints.classroom import (
    router as classroom_router,
)
from app.api.v1.endpoints.timetable import (
    router as timetable_router,
)
from app.api.v1.endpoints.timetable_entry import (
    router as timetable_entry_router,
)
from app.api.v1.endpoints.teacher_substitution import (
    router as teacher_substitution_router,
)
from app.api.student.student_controller import (
    router as student_router,
)
from app.api.student.student_promotion_controller import (
    router as student_promotion_router,
)
from app.api.section.section_controller import (
    router as section_router,
)
from app.api.teacher.teacher_controller import (
    router as teacher_router,
)
from app.common.constants.api_tags import APITags
from app.identity.api.auth import (
    router as auth_router,
)
from app.identity.api.roles import (
    router as roles_router,
)
from app.identity.api.permissions import (
    router as permissions_router,
)
from app.identity.api.user_roles import (
    router as user_roles_router,
)
from app.identity.api.role_permissions import (
    router as role_permissions_router,
)
from app.identity.api.seed import (
    router as seed_router,
)
from app.identity.api.users import (
    router as users_router,
)

api_router = APIRouter()

api_router.include_router(
    school_router,
    prefix="/schools",
    tags=["Schools"],
)

api_router.include_router(
    parent_router,
    prefix="/parents",
    tags=["Parents"],
)

api_router.include_router(
    academic_year_router,
    prefix="/academic-years",
    tags=["Academic Years"],
)

api_router.include_router(
    academic_term_router,
    prefix="/academic-terms",
    tags=["Academic Terms"],
)

api_router.include_router(
    class_progression_rule_router,
    prefix="/progression-matrix",
    tags=["Progression Matrix"],
)

api_router.include_router(
    attendance_router,
    prefix="/attendance",
    tags=[APITags.ATTENDANCE],
)

api_router.include_router(
    school_class_router,
    prefix="/school-classes",
    tags=["School Classes"],
)

api_router.include_router(
    student_router,
    prefix="/students",
    tags=["Students"],
)

api_router.include_router(
    student_promotion_router,
    prefix="/students",
    tags=["Students"],
)


api_router.include_router(
    section_router,
    prefix="/sections",
    tags=["Sections"],
)

api_router.include_router(
    teacher_router,
    prefix="/teachers",
    tags=["Teachers"],
)

api_router.include_router(
    subject_router,
    prefix="/subjects",
    tags=["Subjects"],
)

api_router.include_router(
    exam_router,
    prefix="/exams",
    tags=[APITags.EXAMS],
)

api_router.include_router(
    exam_schedule_router,
    prefix="/exam-schedules",
    tags=[APITags.EXAMS],
)

api_router.include_router(
    student_exam_result_router,
    prefix="/student-exam-results",
    tags=[APITags.EXAMS],
)

api_router.include_router(
    fees_router,
    prefix="/fees",
    tags=[APITags.FEES],
)

api_router.include_router(
    grading_scale_router,
    prefix="/grading-scales",
    tags=["Grading Scales"],
)

api_router.include_router(
    evaluation_config_router,
    prefix="/evaluation-configs",
    tags=["Evaluation Configs"],
)

api_router.include_router(
    report_card_router,
    prefix="/report-cards",
    tags=["Report Cards"],
)

api_router.include_router(
    period_slot_router,
    prefix="/period-slots",
    tags=["Timetable"],
)

api_router.include_router(
    classroom_router,
    prefix="/classrooms",
    tags=["Timetable"],
)

api_router.include_router(
    timetable_router,
    prefix="/timetables",
    tags=["Timetable"],
)

api_router.include_router(
    timetable_entry_router,
    prefix="/timetable-entries",
    tags=["Timetable"],
)

api_router.include_router(
    teacher_substitution_router,
    prefix="/teacher-substitutions",
    tags=["Timetable Substitutions"],
)




api_router.include_router(
    auth_router,
    tags=["Authentication"],
)

api_router.include_router(
    roles_router,
)

api_router.include_router(
    permissions_router,
)

api_router.include_router(
    user_roles_router,
)

api_router.include_router(
    role_permissions_router,
)

api_router.include_router(
    seed_router,
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["Users"],
)
