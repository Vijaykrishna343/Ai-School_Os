from enum import Enum


class PeriodType(str, Enum):
    """
    Type of a school period slot.
    """

    REGULAR = "REGULAR"
    BREAK = "BREAK"
    ASSEMBLY = "ASSEMBLY"
    LUNCH = "LUNCH"


class RoomType(str, Enum):
    """
    Type of a physical classroom or facility.
    """

    CLASSROOM = "CLASSROOM"
    LABORATORY = "LABORATORY"
    AUDITORIUM = "AUDITORIUM"
    SPORTS_GROUND = "SPORTS_GROUND"


class TimetableStatus(str, Enum):
    """
    Status of a timetable.
    """

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class DayOfWeek(str, Enum):
    """
    Days of the week.
    """

    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"
