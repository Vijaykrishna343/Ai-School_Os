from enum import Enum


class BookCopyStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ISSUED = "ISSUED"
    RESERVED = "RESERVED"
    MAINTENANCE = "MAINTENANCE"
    LOST = "LOST"
    DAMAGED = "DAMAGED"
    WRITTEN_OFF = "WRITTEN_OFF"


class BookCondition(str, Enum):
    NEW = "NEW"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"


class LibraryMemberType(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    STAFF = "STAFF"


class LibraryMemberStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class BookLoanStatus(str, Enum):
    ISSUED = "ISSUED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"
    LOST = "LOST"
    DAMAGED = "DAMAGED"


class BookReservationStatus(str, Enum):
    PENDING = "PENDING"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class LibraryFineReason(str, Enum):
    OVERDUE = "OVERDUE"
    DAMAGED_BOOK = "DAMAGED_BOOK"
    LOST_BOOK = "LOST_BOOK"
    OTHER = "OTHER"


class LibraryFineStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    WAIVED = "WAIVED"
