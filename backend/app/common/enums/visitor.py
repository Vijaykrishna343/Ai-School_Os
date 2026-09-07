from enum import Enum


class IdProofType(str, Enum):
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    PASSPORT = "PASSPORT"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    VOTER_ID = "VOTER_ID"
    OTHER = "OTHER"


class VisitorStatus(str, Enum):
    EXPECTED = "EXPECTED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class HostType(str, Enum):
    TEACHER = "TEACHER"
    STAFF = "STAFF"
    STUDENT = "STUDENT"
    OTHER = "OTHER"


class ReceptionInquiryStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"
