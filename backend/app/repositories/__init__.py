from .academic_year.academic_year_repository import (
    AcademicYearRepository,
    academic_year_repository,
)
from .base import BaseRepository
from .fees.fee_payment_repository import (
    FeePaymentRepository,
    fee_payment_repository,
)
from .fees.fee_structure_repository import (
    FeeStructureRepository,
    fee_structure_repository,
)
from .fees.student_fee_assignment_repository import (
    StudentFeeAssignmentRepository,
    student_fee_assignment_repository,
)
from .parent.parent_repository import (
    ParentRepository,
    parent_repository,
)
from .school.school_repository import (
    SchoolRepository,
    school_repository,
)
from .school_class.school_class_repository import (
    SchoolClassRepository,
    school_class_repository,
)
from .section.section_repository import (
    SectionRepository,
    section_repository,
)
from .student.student_repository import (
    StudentRepository,
    student_repository,
)
from .subject.subject_repository import (
    SubjectRepository,
    subject_repository,
)
from .teacher.teacher_repository import (
    TeacherRepository,
    teacher_repository,
)
from .attendance.attendance_repository import (
    AttendanceRepository,
    attendance_repository,
)

__all__ = [
    # Base
    "BaseRepository",
    # Repository classes
    "AcademicYearRepository",
    "ParentRepository",
    "SchoolRepository",
    "SchoolClassRepository",
    "SectionRepository",
    "StudentRepository",
    "SubjectRepository",
    "TeacherRepository",
    "AttendanceRepository",
    "FeeStructureRepository",
    "StudentFeeAssignmentRepository",
    "FeePaymentRepository",
    # Singleton instances
    "academic_year_repository",
    "parent_repository",
    "school_repository",
    "school_class_repository",
    "section_repository",
    "student_repository",
    "subject_repository",
    "teacher_repository",
    "attendance_repository",
    "fee_structure_repository",
    "student_fee_assignment_repository",
    "fee_payment_repository",
]
