from enum import Enum


class ExamType(str, Enum):
    REGULAR = "REGULAR"
    RETEST = "RETEST"
    OTHER = "OTHER"


class ExamStatus(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
