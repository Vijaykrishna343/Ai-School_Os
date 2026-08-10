from .exam_repository import ExamRepository, exam_repository
from .exam_schedule_repository import (
    ExamScheduleRepository,
    exam_schedule_repository,
)
from .student_exam_result_repository import (
    StudentExamResultRepository,
    student_exam_result_repository,
)

__all__ = [
    "ExamRepository",
    "exam_repository",
    "ExamScheduleRepository",
    "exam_schedule_repository",
    "StudentExamResultRepository",
    "student_exam_result_repository",
]
