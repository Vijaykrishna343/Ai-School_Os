from enum import Enum


class SchoolStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    ARCHIVED = "ARCHIVED"