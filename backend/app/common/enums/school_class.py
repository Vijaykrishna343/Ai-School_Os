from enum import Enum


class SchoolClassStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"