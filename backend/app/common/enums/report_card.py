from enum import Enum


class CalculationMode(str, Enum):
    """
    Calculation mode for student report cards.
    """

    SIMPLE_TOTAL = "SIMPLE_TOTAL"
    WEIGHTED_ASSESSMENT_TYPE = "WEIGHTED_ASSESSMENT_TYPE"


class RetestPolicy(str, Enum):
    """
    Policy for handling RETEST and MAKEUP exam attempts.
    """

    REPLACE_ORIGINAL = "REPLACE_ORIGINAL"
    BEST_ATTEMPT = "BEST_ATTEMPT"
    LATEST_ATTEMPT = "LATEST_ATTEMPT"


class RoundingMode(str, Enum):
    """
    Rounding mode for report card percentage and marks.
    """

    ROUND_HALF_UP = "ROUND_HALF_UP"
    ROUND_FLOOR = "ROUND_FLOOR"
    ROUND_CEIL = "ROUND_CEIL"


class ReportCardStatus(str, Enum):
    """
    Lifecycle status of a student report card.
    """

    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"
    PUBLISHED = "PUBLISHED"
