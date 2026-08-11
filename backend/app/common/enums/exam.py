from enum import Enum


class AssessmentType(str, Enum):
    FORMATIVE_ASSESSMENT = "FORMATIVE_ASSESSMENT"
    SUMMATIVE_ASSESSMENT = "SUMMATIVE_ASSESSMENT"
    UNIT_TEST = "UNIT_TEST"
    PERIODIC_TEST = "PERIODIC_TEST"
    QUARTERLY = "QUARTERLY"
    HALF_YEARLY = "HALF_YEARLY"
    TERM = "TERM"
    PRE_FINAL = "PRE_FINAL"
    QUARTER_FINAL = "QUARTER_FINAL"
    SEMI_FINAL = "SEMI_FINAL"
    FINAL = "FINAL"
    OTHER = "OTHER"


class AttemptType(str, Enum):
    REGULAR = "REGULAR"
    RETEST = "RETEST"
    MAKEUP = "MAKEUP"


class ExamStatus(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


def parse_legacy_exam_type(value: str) -> tuple[AssessmentType, AttemptType]:
    """
    Deprecated compatibility helper for parsing legacy exam_type input values.

    Validates that the input is strictly one of: REGULAR, RETEST, OTHER.
    Returns (assessment_type, attempt_type).
    """
    normalized = value.strip().upper()
    if normalized == "REGULAR":
        return (AssessmentType.OTHER, AttemptType.REGULAR)
    elif normalized == "RETEST":
        return (AssessmentType.OTHER, AttemptType.RETEST)
    elif normalized == "OTHER":
        return (AssessmentType.OTHER, AttemptType.REGULAR)
    else:
        raise ValueError(
            f"Invalid legacy exam_type '{value}'. Allowed legacy values: REGULAR, RETEST, OTHER."
        )
