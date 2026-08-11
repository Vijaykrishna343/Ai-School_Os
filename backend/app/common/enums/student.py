from enum import Enum


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class BloodGroup(str, Enum):
    A_POSITIVE = "A_POSITIVE"
    A_NEGATIVE = "A_NEGATIVE"
    B_POSITIVE = "B_POSITIVE"
    B_NEGATIVE = "B_NEGATIVE"
    AB_POSITIVE = "AB_POSITIVE"
    AB_NEGATIVE = "AB_NEGATIVE"
    O_POSITIVE = "O_POSITIVE"
    O_NEGATIVE = "O_NEGATIVE"
    UNKNOWN = "UNKNOWN"


class StudentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TRANSFERRED = "TRANSFERRED"
    PASSED_OUT = "PASSED_OUT"
    DROPPED = "DROPPED"
    GRADUATED = "GRADUATED"
    WITHDRAWN = "WITHDRAWN"


class AdmissionType(str, Enum):
    NEW = "NEW"
    TRANSFER = "TRANSFER"
    RE_ADMISSION = "RE_ADMISSION"


class EnrollmentStatus(str, Enum):
    ENROLLED = "ENROLLED"
    PROMOTED = "PROMOTED"
    RETAINED = "RETAINED"
    GRADUATED = "GRADUATED"
    TRANSFERRED = "TRANSFERRED"
    WITHDRAWN = "WITHDRAWN"
    COMPLETED = "COMPLETED"


class PromotionDecision(str, Enum):
    PENDING = "PENDING"
    PROMOTED = "PROMOTED"
    RETAINED = "RETAINED"
    GRADUATED = "GRADUATED"
    TRANSFERRED = "TRANSFERRED"
    WITHDRAWN = "WITHDRAWN"


class TransferCertificateStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    CANCELLED = "CANCELLED"