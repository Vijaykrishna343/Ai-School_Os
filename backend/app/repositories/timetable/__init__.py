from app.repositories.timetable.period_slot_repository import (
    PeriodSlotRepository,
    period_slot_repository,
)
from app.repositories.timetable.classroom_repository import (
    ClassroomRepository,
    classroom_repository,
)
from app.repositories.timetable.timetable_repository import (
    TimetableRepository,
    timetable_repository,
)
from app.repositories.timetable.timetable_entry_repository import (
    TimetableEntryRepository,
    timetable_entry_repository,
)
from app.repositories.timetable.teacher_substitution_repository import (
    TeacherSubstitutionRepository,
    teacher_substitution_repository,
)

__all__ = [
    "PeriodSlotRepository",
    "period_slot_repository",
    "ClassroomRepository",
    "classroom_repository",
    "TimetableRepository",
    "timetable_repository",
    "TimetableEntryRepository",
    "timetable_entry_repository",
    "TeacherSubstitutionRepository",
    "teacher_substitution_repository",
]
