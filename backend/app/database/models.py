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
from app.models.academic_year import AcademicYear
from app.models.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.subject.subject import Subject
from app.models.exam import Exam, ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading import GradeScale, GradeScaleEntry

# ==========================
# Identity Models
# ==========================

from app.identity.models import (
    IdentityUser,
    IdentityRole,
    IdentityPermission,
    IdentityUserRole,
    IdentityRolePermission,
)

__all__ = [
    "School",
    "Parent",
    "AcademicYear",
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
]
