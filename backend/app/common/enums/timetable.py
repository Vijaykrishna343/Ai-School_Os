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
